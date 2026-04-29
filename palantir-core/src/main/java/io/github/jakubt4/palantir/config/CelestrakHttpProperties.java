package io.github.jakubt4.palantir.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * HTTP client timeouts for outbound calls to <a href="https://celestrak.org">CelesTrak</a>'s
 * GP catalogue endpoint, used by the TLE auto-refresh scheduler.
 *
 * <p>Bound from {@code palantir.http.celestrak.*} in {@code application.yaml}.
 * Both fields use Spring Boot's {@link Duration} binder which accepts the
 * suffix forms {@code 5s}, {@code 100ms}, {@code 2m}, {@code 1h}, … on top
 * of ISO-8601.
 *
 * @param connectTimeout
 *   How long the client waits to establish a TCP/TLS connection before
 *   giving up. <strong>5 s default</strong>: a healthy resolver + handshake
 *   to a public CDN-fronted endpoint normally completes under 1 s; the 5×
 *   margin absorbs slow DNS, congested last-mile, or transient route flaps
 *   without false-failing the refresh. Tighten (≤ 2 s) only if the call is
 *   on the critical path of a user-visible operation.
 *
 * @param readTimeout
 *   How long the client waits for response bytes once connected, per read.
 *   <strong>10 s default</strong>: the TLE body is ~150 bytes so a fast
 *   response is sub-100 ms; the headroom covers "endpoint accepted the
 *   connection but upstream data source stalled" failure modes seen on
 *   public catalogues during update windows. Must remain well below the
 *   scheduler interval (6 h here) so a stuck call cannot pin the
 *   scheduler thread across the next tick.
 */
@ConfigurationProperties(prefix = "palantir.http.celestrak")
public record CelestrakHttpProperties(
        Duration connectTimeout,
        Duration readTimeout
) {
}
