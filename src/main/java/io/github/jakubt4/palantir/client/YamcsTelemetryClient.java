package io.github.jakubt4.palantir.client;

import io.github.jakubt4.palantir.dto.ParameterValue;
import io.github.jakubt4.palantir.dto.YamcsParameterRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.List;

@Slf4j
@Service
public class YamcsTelemetryClient {

    private static final String BATCH_SET_PATH = "/api/processors/palantir/realtime/parameters:batchSet";

    private final RestClient restClient;

    public YamcsTelemetryClient(final RestClient.Builder restClientBuilder,
                               @Value("${yamcs.base-url}") final String baseUrl) {
        this.restClient = restClientBuilder
                .baseUrl(baseUrl)
                .build();
    }

    @Retryable(retryFor = RestClientException.class, maxAttempts = 3,
               backoff = @Backoff(delay = 500, maxDelay = 2000))
    public void sendTelemetry(final double latitude, final double longitude, final double altitude) {
        final var request = new YamcsParameterRequest(List.of(
                ParameterValue.of("/Palantir/Latitude", latitude),
                ParameterValue.of("/Palantir/Longitude", longitude),
                ParameterValue.of("/Palantir/Altitude", altitude)
        ));

        restClient.post()
                .uri(BATCH_SET_PATH)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .toBodilessEntity();
    }

    @Recover
    public void recoverSendTelemetry(final RestClientException e,
                                     final double latitude, final double longitude, final double altitude) {
        log.warn("Failed to send telemetry to Yamcs after retries: {}", e.getMessage());
    }
}
