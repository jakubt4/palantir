package io.github.jakubt4.palantir;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Palantir — Digital Twin ground segment for LEO satellite operations.
 *
 * <p>Propagates a satellite orbit using Orekit SGP4/SDP4 from ingested TLE data,
 * encodes geodetic telemetry into CCSDS Space Packets (CCSDS 133.0-B-1),
 * and streams them over UDP to a Yamcs mission control instance.
 *
 * @see io.github.jakubt4.palantir.service.OrbitPropagationService
 * @see io.github.jakubt4.palantir.service.CcsdsTelemetrySender
 */
@SpringBootApplication
@EnableScheduling
public class PalantirApplication {

    public static void main(String[] args) {
        SpringApplication.run(PalantirApplication.class, args);
    }
}
