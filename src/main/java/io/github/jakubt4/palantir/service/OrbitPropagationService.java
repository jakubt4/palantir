package io.github.jakubt4.palantir.service;

import io.github.jakubt4.palantir.client.YamcsTelemetryClient;
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

@Slf4j
@Service
@RequiredArgsConstructor
public class OrbitPropagationService {

    @SuppressWarnings("unused") // injected to guarantee Orekit data is loaded before @PostConstruct
    private final OrekitConfig orekitConfig;
    private final YamcsTelemetryClient yamcsTelemetryClient;

    private final AtomicReference<TLEPropagator> activePropagator = new AtomicReference<>();
    private final AtomicReference<String> activeSatelliteName = new AtomicReference<>("NONE");

    private OneAxisEllipsoid earth;

    @PostConstruct
    void initEarthModel() {
        final var itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, true);
        earth = new OneAxisEllipsoid(
                Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                Constants.WGS84_EARTH_FLATTENING,
                itrf
        );
        log.info("Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010");
    }

    public void updateTle(final String satelliteName, final String line1, final String line2) {
        final var tle = new TLE(line1, line2);
        final var propagator = TLEPropagator.selectExtrapolator(tle);

        activePropagator.set(propagator);
        activeSatelliteName.set(satelliteName);

        log.info("AOS — Acquired signal for [{}], TLE epoch: {}, propagator: {}",
                satelliteName, tle.getDate(), propagator.getClass().getSimpleName());
    }

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

            log.info("[{}] Position — lat={} °, lon={} °, alt={} km",
                    activeSatelliteName.get(),
                    String.format("%.2f", latDeg),
                    String.format("%.2f", lonDeg),
                    String.format("%.2f", altKm));

            yamcsTelemetryClient.sendTelemetry(latDeg, lonDeg, altKm);
        } catch (final Exception e) {
            log.error("[{}] Propagation error: {}", activeSatelliteName.get(), e.getMessage());
        }
    }
}
