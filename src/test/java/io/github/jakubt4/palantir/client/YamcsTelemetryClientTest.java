package io.github.jakubt4.palantir.client;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestTemplate;

import org.springframework.web.client.HttpServerErrorException;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class YamcsTelemetryClientTest {

    private static final String BASE_URL = "http://localhost:8090";

    private YamcsTelemetryClient client;
    private MockRestServiceServer mockServer;

    @BeforeEach
    void setUp() {
        final var restTemplate = new RestTemplate();
        mockServer = MockRestServiceServer.bindTo(restTemplate).build();

        final var builder = RestClient.builder()
                .requestFactory(restTemplate.getRequestFactory());

        client = new YamcsTelemetryClient(builder, BASE_URL);
    }

    @Test
    void sendTelemetryPostsCorrectJsonToBatchSetEndpoint() {
        mockServer.expect(requestTo(BASE_URL + "/api/processors/palantir/realtime/parameters:batchSet"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.request[0].id.name").value("/Palantir/Latitude"))
                .andExpect(jsonPath("$.request[1].id.name").value("/Palantir/Longitude"))
                .andExpect(jsonPath("$.request[2].id.name").value("/Palantir/Altitude"))
                .andExpect(jsonPath("$.request[0].value.type").value("FLOAT"))
                .andExpect(jsonPath("$.request[1].value.type").value("FLOAT"))
                .andExpect(jsonPath("$.request[2].value.type").value("FLOAT"))
                .andRespond(withSuccess());

        client.sendTelemetry(51.5, -0.1, 408.0);

        mockServer.verify();
    }

    @Test
    void sendTelemetryThrowsOnServerError() {
        mockServer.expect(requestTo(BASE_URL + "/api/processors/palantir/realtime/parameters:batchSet"))
                .andRespond(withServerError());

        assertThatThrownBy(() -> client.sendTelemetry(51.5, -0.1, 408.0))
                .isInstanceOf(HttpServerErrorException.class);
    }
}
