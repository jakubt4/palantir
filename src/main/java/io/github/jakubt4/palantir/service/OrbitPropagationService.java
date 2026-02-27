package io.github.jakubt4.palantir.service;

import io.github.jakubt4.palantir.config.OrekitConfig;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.orekit.bodies.OneAxisEllipsoid;
import org.orekit.frames.FramesFactory;
import org.orekit.propagation.analytical.tle.TLE;
import org.orekit.propagation.analytical.tle.TLEPropagator;
import org.orekit.time.AbsoluteDate;
import org.orekit.time.TimeScalesFactory;
import org.orekit.utils.Constants;
import org.orekit.utils.IERSConventions;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Date;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Core orbit propagation engine — drives the satellite digital twin.
 *
 * <p>Maintains a thread-safe {@link TLEPropagator} that can be hot-swapped at runtime
 * via {@link #updateTle}. A {@code @Scheduled} loop propagates the current TLE at 1 Hz,
 * converts the spacecraft state from TEME to geodetic coordinates (WGS-84), and hands
 * lat/lon/alt to {@link CcsdsTelemetrySender} for CCSDS downlink.
 *
 * <p>On startup a default ISS TLE is loaded so telemetry flows immediately.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OrbitPropagationService {

    // Default ISS TLE for immediate out-of-the-box propagation
    private static final String DEFAULT_SAT_NAME = "ISS (ZARYA)";
    private static final String DEFAULT_TLE_LINE1 =
            "1 25544U 98067A   26046.82773376  .00012360  00000+0  23475-3 0  9996";
    private static final String DEFAULT_TLE_LINE2 =
            "2 25544  51.6318 180.4216 0010986 102.2508 257.9711 15.48632468552944";

    @SuppressWarnings("unused") // injected to guarantee Orekit data is loaded before @PostConstruct
    private final OrekitConfig orekitConfig;
    private final CcsdsTelemetrySender ccsdsTelemetrySender;

    private final AtomicReference<TLEPropagator> activePropagator = new AtomicReference<>();
    private final AtomicReference<String> activeSatelliteName = new AtomicReference<>("NONE");

    private OneAxisEllipsoid earth;

    @PostConstruct
    void init() {
        final var itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, true);
        earth = new OneAxisEllipsoid(
                Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                Constants.WGS84_EARTH_FLATTENING,
                itrf
        );
        log.info("Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010");

        loadDefaultTle();
    }

    private void loadDefaultTle() {
        try {
            updateTle(DEFAULT_SAT_NAME, DEFAULT_TLE_LINE1, DEFAULT_TLE_LINE2);
            log.info("Default TLE loaded — propagation active for [{}]", DEFAULT_SAT_NAME);
        } catch (final Exception e) {
            log.warn("Failed to load default TLE, awaiting manual ingestion: {}", e.getMessage());
        }
    }

    /**
     * Parses a TLE and atomically replaces the active propagator.
     *
     * @param satelliteName display name for logging
     * @param line1         NORAD TLE line 1
     * @param line2         NORAD TLE line 2
     * @throws org.orekit.errors.OrekitException if the TLE cannot be parsed
     */
    public void updateTle(final String satelliteName, final String line1, final String line2) {
        final var tle = new TLE(line1, line2);
        final var propagator = TLEPropagator.selectExtrapolator(tle);

        activePropagator.set(propagator);
        activeSatelliteName.set(satelliteName);

        log.info("AOS — Acquired signal for [{}], TLE epoch: {}, propagator: {}",
                satelliteName, tle.getDate(), propagator.getClass().getSimpleName());
    }

    /**
     * Propagates the active TLE to the current wall-clock instant, converts
     * the resulting spacecraft position to geodetic coordinates, and transmits
     * a CCSDS telemetry packet. Invoked every second by Spring's scheduler.
     */
    @Scheduled(fixedRate = 1000)
    public void propagateAndSend() {
        final var propagator = activePropagator.get();
        if (propagator == null) {
            log.debug("WAITING_FOR_TLE — No active propagator, awaiting TLE ingestion");
            return;
        }

        try {
            final var now = new AbsoluteDate(Date.from(Instant.now()), TimeScalesFactory.getUTC());

            final var state = propagator.propagate(now);
            final var position = state.getPVCoordinates(earth.getBodyFrame()).getPosition();
            final var geo = earth.transform(position, earth.getBodyFrame(), now);

            final var latDeg = Math.toDegrees(geo.getLatitude());
            final var lonDeg = Math.toDegrees(geo.getLongitude());
            final var altKm = geo.getAltitude() / 1000.0;

            log.info("[{}] Position — lat={} deg, lon={} deg, alt={} km",
                    activeSatelliteName.get(),
                    String.format("%.2f", latDeg),
                    String.format("%.2f", lonDeg),
                    String.format("%.2f", altKm));

            ccsdsTelemetrySender.sendPacket((float) latDeg, (float) lonDeg, (float) altKm);
        } catch (final Exception e) {
            log.error("[{}] Propagation error: {}", activeSatelliteName.get(), e.getMessage());
        }
    }
}
