package io.github.jakubt4.palantir.controller;

import io.github.jakubt4.palantir.dto.TleRequest;
import io.github.jakubt4.palantir.dto.TleResponse;
import io.github.jakubt4.palantir.service.OrbitPropagationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * REST endpoint for Two-Line Element (TLE) ingestion.
 *
 * <p>Accepts a satellite TLE via {@code POST /api/orbit/tle} and hot-swaps
 * the active orbit propagator, enabling in-flight target changes without restart.
 */
@Slf4j
@RestController
@RequestMapping("/api/orbit")
@RequiredArgsConstructor
public class TleIngestionController {

    private final OrbitPropagationService orbitPropagationService;

    /**
     * Ingests a TLE set and activates orbit propagation for the given satellite.
     *
     * @param request satellite name and two-line element strings
     * @return {@code 200 OK} with ACTIVE status on success, {@code 400 Bad Request} on
     *         validation failure or Orekit parse error
     */
    @PostMapping("/tle")
    public ResponseEntity<TleResponse> ingestTle(@RequestBody final TleRequest request) {
        if (request.satelliteName() == null || request.satelliteName().isBlank()) {
            return ResponseEntity.badRequest()
                    .body(new TleResponse(null, "REJECTED", "Satellite name is required"));
        }
        if (request.line1() == null || request.line2() == null) {
            return ResponseEntity.badRequest()
                    .body(new TleResponse(request.satelliteName(), "REJECTED", "TLE line1 and line2 are required"));
        }

        try {
            orbitPropagationService.updateTle(request.satelliteName(), request.line1(), request.line2());
            log.info("TLE ingested for satellite [{}]", request.satelliteName());
            return ResponseEntity.ok(
                    new TleResponse(request.satelliteName(), "ACTIVE", "TLE loaded, propagation started"));
        } catch (final Exception e) {
            log.error("Failed to parse TLE for [{}]: {}", request.satelliteName(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(new TleResponse(request.satelliteName(), "REJECTED", "Invalid TLE: " + e.getMessage()));
        }
    }
}
