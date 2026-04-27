package io.github.jakubt4.palantir.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.List;

/**
 * Background scheduler that keeps the active TLE current by polling
 * CelesTrak's GP catalog. Without this, the propagator extrapolates
 * further and further from the originally-loaded TLE epoch — SGP4
 * accuracy degrades at the order of km/day, visible on the PAL-101
 * ground-track HMI as the spacecraft rendering "in the wrong place".
 *
 * <p>Hot-swap goes through the existing {@link OrbitPropagationService#updateTle}
 * mechanism, so the live 1 Hz telemetry pipeline continues uninterrupted
 * across the refresh.
 *
 * <p>Gated by {@code palantir.tle.refresh.enabled}; the test profile
 * sets this to {@code false} so unit tests do not hit the network.
 */
@Slf4j
@Service
@ConditionalOnProperty(
        prefix = "palantir.tle.refresh",
        name = "enabled",
        havingValue = "true",
        matchIfMissing = true
)
public class TleRefreshService {

    private final OrbitPropagationService orbitPropagationService;
    private final RestClient restClient;

    @Value("${palantir.tle.refresh.celestrak-url:https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle}")
    private String celestrakUrl;

    @Value("${palantir.tle.refresh.satellite-name:ISS (ZARYA)}")
    private String satelliteName;

    public TleRefreshService(final OrbitPropagationService orbitPropagationService,
                             final RestClient.Builder restClientBuilder) {
        this.orbitPropagationService = orbitPropagationService;
        this.restClient = restClientBuilder.build();
    }

    /**
     * Default cadence 6 h — CelesTrak rate-limit-friendly, and ISS TLEs
     * publish roughly daily so 6 h is the natural sub-daily cadence.
     * Initial delay 1 min after startup so the default TLE has a moment
     * to load and we don't pile up on the first scheduler tick.
     */
    @Scheduled(
            fixedRateString = "${palantir.tle.refresh.interval-ms:21600000}",
            initialDelayString = "${palantir.tle.refresh.initial-delay-ms:60000}"
    )
    public void refreshTle() {
        try {
            final var body = fetchTleBody();
            applyTle(body);
        } catch (final RestClientException e) {
            log.warn("TLE refresh: HTTP failure fetching {}: {}", celestrakUrl, e.getMessage());
        }
    }

    /**
     * Network call extracted so unit tests can stub it via {@code Mockito.spy()}.
     */
    String fetchTleBody() {
        return restClient.get()
                .uri(celestrakUrl)
                .retrieve()
                .body(String.class);
    }

    /**
     * Parse a CelesTrak GP-format TLE body and push it through the propagator
     * hot-swap. Robust to both 3-line (name + line1 + line2) and 2-line
     * (line1 + line2) responses — takes the last two non-blank lines as
     * the orbital elements. Orekit parse failures are caught and logged
     * so a single bad fetch doesn't crash the service.
     */
    void applyTle(final String body) {
        if (body == null || body.isBlank()) {
            log.warn("TLE refresh: empty response body, skipping");
            return;
        }

        final List<String> lines = body.lines()
                .map(String::strip)
                .filter(l -> !l.isEmpty())
                .toList();
        if (lines.size() < 2) {
            log.warn("TLE refresh: only {} non-blank line(s) in response, skipping", lines.size());
            return;
        }

        final var line1 = lines.get(lines.size() - 2);
        final var line2 = lines.get(lines.size() - 1);

        try {
            orbitPropagationService.updateTle(satelliteName, line1, line2);
            log.info("TLE refresh: refreshed [{}] from CelesTrak", satelliteName);
        } catch (final Exception e) {
            log.warn("TLE refresh: parse error for response from {}: {}", celestrakUrl, e.getMessage());
        }
    }
}
