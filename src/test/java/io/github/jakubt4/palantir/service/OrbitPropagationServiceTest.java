package io.github.jakubt4.palantir.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.verify;

@SpringBootTest
class OrbitPropagationServiceTest {

    // Valid ISS TLE (epoch 2008-264, checksum-verified)
    private static final String TLE_LINE1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927";
    private static final String TLE_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537";

    @MockBean
    private CcsdsTelemetrySender ccsdsTelemetrySender;

    @Autowired
    private OrbitPropagationService orbitPropagationService;

    @BeforeEach
    void resetMock() {
        Mockito.clearInvocations(ccsdsTelemetrySender);
    }

    @Test
    void initializesEarthModelSuccessfully() {
        assertThat(orbitPropagationService).isNotNull();
    }

    @Test
    void propagateAndSendTransmitsAfterTleIngestion() {
        orbitPropagationService.updateTle("ISS (ZARYA)", TLE_LINE1, TLE_LINE2);
        orbitPropagationService.propagateAndSend();

        final var latCaptor = ArgumentCaptor.forClass(Float.class);
        final var lonCaptor = ArgumentCaptor.forClass(Float.class);
        final var altCaptor = ArgumentCaptor.forClass(Float.class);

        verify(ccsdsTelemetrySender, atLeastOnce())
                .sendPacket(latCaptor.capture(), lonCaptor.capture(), altCaptor.capture());

        // Latitude must be within physical bounds (ISS inclination ~51.6°)
        assertThat(latCaptor.getAllValues()).allSatisfy(lat ->
                assertThat((double) lat).isBetween(-90.0, 90.0));

        // Longitude within valid range
        assertThat(lonCaptor.getAllValues()).allSatisfy(lon ->
                assertThat((double) lon).isBetween(-180.0, 180.0));

        // Altitude must be positive
        assertThat(altCaptor.getAllValues()).allSatisfy(alt ->
                assertThat((double) alt).isGreaterThan(0.0));
    }
}
