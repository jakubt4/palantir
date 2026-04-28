package io.github.jakubt4.palantir.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.ClientHttpRequestFactories;
import org.springframework.boot.web.client.ClientHttpRequestFactorySettings;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

/**
 * Builds named {@link RestClient} beans for outbound HTTP traffic. Each
 * upstream gets its own bean + qualifier so timeouts can be tuned per
 * service and so unrelated callers do not share a request factory.
 *
 * <p>The underlying request factory is {@link JdkClientHttpRequestFactory},
 * a thin Spring wrapper around Java 11+ {@link java.net.http.HttpClient}.
 * It supports HTTP/2, has built-in connection pooling, and avoids the
 * legacy {@code HttpURLConnection} stack used by
 * {@code SimpleClientHttpRequestFactory}.
 */
@Configuration
@EnableConfigurationProperties(CelestrakHttpProperties.class)
public class RestClientConfiguration {

    /** Qualifier for the {@link RestClient} configured for CelesTrak GP catalogue calls. */
    public static final String CELESTRAK_REST_CLIENT = "celestrakRestClient";

    @Bean(name = CELESTRAK_REST_CLIENT)
    public RestClient celestrakRestClient(final CelestrakHttpProperties properties) {
        // ClientHttpRequestFactorySettings + ClientHttpRequestFactories together
        // hide the API quirk that JdkClientHttpRequestFactory's connect timeout is
        // configured on the underlying HttpClient (not on the factory itself, as
        // it would be on the legacy SimpleClientHttpRequestFactory).
        final var settings = ClientHttpRequestFactorySettings.DEFAULTS
                .withConnectTimeout(properties.connectTimeout())
                .withReadTimeout(properties.readTimeout());
        final var factory = ClientHttpRequestFactories.get(JdkClientHttpRequestFactory.class, settings);
        return RestClient.builder()
                .requestFactory(factory)
                .build();
    }
}
