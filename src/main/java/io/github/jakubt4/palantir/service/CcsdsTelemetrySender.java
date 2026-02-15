package io.github.jakubt4.palantir.service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Encodes and transmits telemetry as raw CCSDS Space Packets (CCSDS 133.0-B-1) over UDP.
 * Yamcs GenericPacketPreprocessor extracts the sequence count and assigns local generation time.
 */
@Slf4j
@Service
public class CcsdsTelemetrySender {

    private static final int APID = 100;
    private static final int CCSDS_HEADER_LENGTH = 6;
    private static final int PAYLOAD_LENGTH = 12; // 3 floats × 4 bytes
    private static final int TOTAL_LENGTH = CCSDS_HEADER_LENGTH + PAYLOAD_LENGTH;

    private final AtomicInteger sequenceCounter = new AtomicInteger(0);

    @Value("${yamcs.udp.host:localhost}")
    private String host;

    @Value("${yamcs.udp.port:10000}")
    private int port;

    private DatagramSocket socket;
    private InetAddress address;

    @PostConstruct
    void init() throws SocketException, UnknownHostException {
        socket = new DatagramSocket();
        address = InetAddress.getByName(host);
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
     * Encodes lat/lon/alt into a CCSDS Space Packet and transmits via UDP.
     *
     * <p>Packet layout (18 bytes total):
     * <pre>
     *   [0-1]   Packet ID:       Version(000) | Type(0) | SecHeader(0) | APID(100)
     *   [2-3]   Sequence Control: Flags(11)    | Count(14-bit auto-increment)
     *   [4-5]   Data Length:      payload_bytes - 1 = 11
     *   [6-9]   Latitude          IEEE 754 float, big-endian
     *   [10-13] Longitude         IEEE 754 float, big-endian
     *   [14-17] Altitude          IEEE 754 float, big-endian
     * </pre>
     */
    public void sendPacket(final float lat, final float lon, final float alt) {
        final var buffer = ByteBuffer.allocate(TOTAL_LENGTH);

        // Packet ID: Version(000) | Type(0) | SecHeader(0) | APID(11 bits)
        final var packetId = (short) (APID & 0x07FF);
        buffer.putShort(packetId);

        // Sequence Control: Grouping Flags(11 = standalone) | Sequence Count(14 bits)
        final var seqCount = sequenceCounter.getAndIncrement() & 0x3FFF;
        final var seqControl = (short) (0xC000 | seqCount);
        buffer.putShort(seqControl);

        // Data Length: octets in Packet Data Field minus 1
        final var dataLength = (short) (PAYLOAD_LENGTH - 1);
        buffer.putShort(dataLength);

        // Payload: 3 × IEEE 754 float, big-endian (ByteBuffer default)
        buffer.putFloat(lat);
        buffer.putFloat(lon);
        buffer.putFloat(alt);

        try {
            final var data = buffer.array();
            final var packet = new DatagramPacket(data, data.length, address, port);
            socket.send(packet);
        } catch (final IOException e) {
            log.error("Failed to transmit CCSDS packet: {}", e.getMessage());
        }
    }
}
