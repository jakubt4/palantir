package io.github.jakubt4.palantir.service;

import io.github.jakubt4.palantir.config.OrekitConfig;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.orekit.time.AbsoluteDate;
import org.orekit.time.DateComponents;
import org.orekit.time.TimeComponents;
import org.orekit.time.TimeScalesFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Encodes and transmits telemetry as raw CCSDS Space Packets (CCSDS 133.0-B-2) over UDP.
 *
 * <p>Packet layout (24 bytes total):
 * <pre>
 *   [0-1]   Packet ID         Version(000) | Type(0) | SecHeader(1) | APID(100)
 *   [2-3]   Sequence Control  Flags(11)    | Count(14-bit auto-increment)
 *   [4-5]   Data Length       octets-in-PDF − 1 = 17
 *   [6-9]   CUC coarse        TAI seconds since 1958-01-01 (uint32 BE)
 *   [10-11] CUC fine          fractional seconds, units of 1/65536 s (uint16 BE)
 *   [12-15] Latitude          IEEE 754 float, big-endian
 *   [16-19] Longitude         IEEE 754 float, big-endian
 *   [20-23] Altitude          IEEE 754 float, big-endian
 * </pre>
 *
 * <p>Yamcs decodes the time on the receive side via
 * {@code org.yamcs.tctm.cfs.CfsPacketPreprocessor} with
 * {@code timeEncoding.epoch: TAI} — that preprocessor reads bytes 6-9 as
 * uint32 coarse + bytes 10-11 as uint16 fine and stamps the packet's
 * generation_time accordingly. This replaces the older
 * {@code useLocalGenerationTime: true} which used ground reception time
 * as a stand-in for spacecraft generation time (CLAUDE.md Rule 26).
 *
 * <p>Time format reference: CCSDS 301.0-B-4 §3.2 (Unsegmented Time Code,
 * Level-1 epoch 1 January 1958 TAI). 4 + 2 octets gives 1/65536 s
 * resolution (~15 µs), well below our 1 Hz cadence.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CcsdsTelemetrySender {

    private static final int APID = 100;
    private static final int CCSDS_PRIMARY_HEADER_LENGTH = 6;
    private static final int CCSDS_SECONDARY_HEADER_LENGTH = 6;  // 4 bytes coarse + 2 bytes fine
    private static final int PAYLOAD_LENGTH = 12;                // 3 floats × 4 bytes
    private static final int TOTAL_LENGTH =
            CCSDS_PRIMARY_HEADER_LENGTH + CCSDS_SECONDARY_HEADER_LENGTH + PAYLOAD_LENGTH;

    private final AtomicInteger sequenceCounter = new AtomicInteger(0);

    @SuppressWarnings("unused")  // injected to guarantee Orekit data is loaded before @PostConstruct
    private final OrekitConfig orekitConfig;

    @Value("${yamcs.udp.host:localhost}")
    private String host;

    @Value("${yamcs.udp.port:10000}")
    private int port;

    private DatagramSocket socket;
    private InetAddress address;
    /** TAI Level-1 epoch — 1958-01-01 00:00:00 TAI. CCSDS 301.0-B-4 §3.2.4. */
    private AbsoluteDate taiEpoch;

    @PostConstruct
    void init() throws SocketException, UnknownHostException {
        socket = new DatagramSocket();
        address = InetAddress.getByName(host);
        taiEpoch = new AbsoluteDate(
                new DateComponents(1958, 1, 1),
                TimeComponents.H00,
                TimeScalesFactory.getTAI()
        );
        log.info("CCSDS Telemetry Link initialized — target={}:{}", host, port);
    }

    @PreDestroy
    void destroy() {
        if (socket != null && !socket.isClosed()) {
            socket.close();
            log.info("CCSDS Telemetry Link closed");
        }
    }

    /**
     * Encodes lat/lon/alt and the supplied generation time into a CCSDS Space Packet
     * with Secondary-Header CUC time and transmits via UDP.
     *
     * @param generationTime spacecraft-side time of the propagation tick that produced
     *                       these coordinates; embedded as TAI seconds since 1958-01-01
     * @param lat latitude (degrees)
     * @param lon longitude (degrees)
     * @param alt altitude (kilometres)
     */
    public void sendPacket(final AbsoluteDate generationTime,
                           final float lat, final float lon, final float alt) {
        final var buffer = ByteBuffer.allocate(TOTAL_LENGTH);

        // Packet ID: Version(000) | Type(0) | SecHeader(1) | APID(11 bits).
        // Sec Header bit (bit 11) is now set because we emit a Secondary Header.
        final var packetId = (short) (0x0800 | (APID & 0x07FF));
        buffer.putShort(packetId);

        // Sequence Control: Grouping Flags(11 = standalone) | Sequence Count(14 bits).
        final var seqCount = sequenceCounter.getAndIncrement() & 0x3FFF;
        final var seqControl = (short) (0xC000 | seqCount);
        buffer.putShort(seqControl);

        // Data Length: octets in Packet Data Field (Sec Header + payload) minus 1.
        final var dataLength = (short) (CCSDS_SECONDARY_HEADER_LENGTH + PAYLOAD_LENGTH - 1);
        buffer.putShort(dataLength);

        // Secondary Header — CUC time, 4 octets coarse + 2 octets fine, no P-field.
        // The CfsPacketPreprocessor on the Yamcs side is configured with TAI epoch and
        // reads (uint32, uint16) directly at offsets 6 and 10.
        final var secondsSinceEpoch = generationTime.durationFrom(taiEpoch);
        final var coarse = (long) Math.floor(secondsSinceEpoch);
        final var fine = (int) Math.round((secondsSinceEpoch - coarse) * 65536.0) & 0xFFFF;
        buffer.putInt((int) (coarse & 0xFFFFFFFFL));
        buffer.putShort((short) fine);

        // Payload: 3 × IEEE 754 float, big-endian (ByteBuffer default).
        buffer.putFloat(lat);
        buffer.putFloat(lon);
        buffer.putFloat(alt);

        try {
            final var data = buffer.array();
            final var packet = new DatagramPacket(data, data.length, address, port);
            socket.send(packet);
            final var hexFmt = HexFormat.ofDelimiter(" ");
            final var hdrHex = hexFmt.formatHex(data, 0, CCSDS_PRIMARY_HEADER_LENGTH);
            final var secHdrHex = hexFmt.formatHex(data,
                    CCSDS_PRIMARY_HEADER_LENGTH,
                    CCSDS_PRIMARY_HEADER_LENGTH + CCSDS_SECONDARY_HEADER_LENGTH);
            final var payloadHex = hexFmt.formatHex(data,
                    CCSDS_PRIMARY_HEADER_LENGTH + CCSDS_SECONDARY_HEADER_LENGTH,
                    TOTAL_LENGTH);
            log.debug("TX CCSDS [APID={}, SEQ={}, {} bytes, t={}] → {}:{} | lat={}, lon={}, alt={} km\n"
                            + "         HDR: [{}]  SEC: [{}]  DATA: [{}]",
                    APID, seqCount, data.length, generationTime, host, port, lat, lon, alt,
                    hdrHex, secHdrHex, payloadHex);
        } catch (final IOException e) {
            log.error("Failed to transmit CCSDS packet: {}", e.getMessage());
        }
    }
}
