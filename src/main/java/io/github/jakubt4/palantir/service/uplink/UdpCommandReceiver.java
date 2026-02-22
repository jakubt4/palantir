package io.github.jakubt4.palantir.service.uplink;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Listens for telecommand packets from the ground station (Yamcs) via UDP.
 * Uses Java 21 Virtual Threads for non-blocking receive.
 */
@Slf4j
@Service
public class UdpCommandReceiver {

    private final int port;
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
    private DatagramSocket socket;
    private volatile boolean running = true;

    public UdpCommandReceiver(@Value("${palantir.uplink.port:10001}") final int port) {
        this.port = port;
    }

    @PostConstruct
    void startListening() {
        executor.submit(() -> {
            try {
                socket = new DatagramSocket(port);
                log.info("[UPLINK] SYSTEM ONLINE | Listening on UDP port {}", socket.getLocalPort());

                final var buffer = new byte[1024];

                while (running) {
                    final var packet = new DatagramPacket(buffer, buffer.length);
                    socket.receive(packet);
                    processTelecommand(packet);
                }
            } catch (final IOException e) {
                if (running) {
                    log.error("[UPLINK] CRITICAL FAILURE: {}", e.getMessage());
                }
            }
        });
    }

    private void processTelecommand(final DatagramPacket packet) {
        final var data = packet.getData();
        final var opCode = data[0];

        final var commandName = switch (opCode) {
            case 0x01 -> "PING / NOOP";
            case 0x02 -> "REBOOT_OBC";
            case 0x03 -> "SET_TRANSMIT_POWER";
            default -> "UNKNOWN_OPCODE (0x" + String.format("%02X", opCode) + ")";
        };

        log.warn("[COMMAND RECEIVED] Source: {}:{} | OpCode: 0x{} | Executing: {}",
                packet.getAddress().getHostAddress(),
                packet.getPort(),
                String.format("%02X", opCode),
                commandName);

        if (opCode == 0x02) {
            triggerRebootSequence();
        }
    }

    private void triggerRebootSequence() {
        log.info("[UPLINK] INITIATING SYSTEM REBOOT SEQUENCE");
    }

    @PreDestroy
    void stop() {
        running = false;
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
        executor.shutdown();
        log.info("[UPLINK] SYSTEM OFFLINE");
    }
}
