package io.github.jakubt4.palantir.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.verify;

/**
 * Unit tests for the TLE auto-refresh scheduler. Network calls and
 * Orekit parsing are not exercised here — those happen in the live
 * smoke test once the service runs against the real CelesTrak. These
 * tests cover the parsing/dispatch logic and the failure paths that
 * matter for keeping the propagator alive when the network is flaky.
 */
@ExtendWith(MockitoExtension.class)
class TleRefreshServiceTest {

    private static final String LINE1 =
            "1 25544U 98067A   26117.42361111  .00009718  00000+0  17738-3 0  9994";
    private static final String LINE2 =
            "2 25544  51.6395 184.8743 0006894  87.2451 272.9056 15.49962834424268";

    @Mock
    private OrbitPropagationService orbitPropagationService;

    @Mock
    private RestClient restClient;

    private TleRefreshService service;

    @BeforeEach
    void setUp() {
        // The CelesTrak RestClient is built upstream by RestClientConfiguration; the
        // service receives a fully-configured instance via @Qualifier injection.
        // Tests don't exercise the network — fetchTleBody() is stubbed via spy in
        // the http-failure case, and applyTle(...) is called directly otherwise.
        service = new TleRefreshService(orbitPropagationService, restClient);
        ReflectionTestUtils.setField(service, "celestrakUrl", "https://example.test/tle");
        ReflectionTestUtils.setField(service, "satelliteName", "ISS (ZARYA)");
    }

    @Test
    void parsesThreeLineCelestrakResponse() {
        final var body = "ISS (ZARYA)\n" + LINE1 + "\n" + LINE2 + "\n";
        service.applyTle(body);
        verify(orbitPropagationService).updateTle(eq("ISS (ZARYA)"), eq(LINE1), eq(LINE2));
    }

    @Test
    void parsesTwoLineResponseWithoutNameHeader() {
        final var body = LINE1 + "\n" + LINE2 + "\n";
        service.applyTle(body);
        verify(orbitPropagationService).updateTle(eq("ISS (ZARYA)"), eq(LINE1), eq(LINE2));
    }

    @Test
    void toleratesBlankAndPaddedLines() {
        final var body = "\n  ISS (ZARYA)  \n\n  " + LINE1 + "  \n  " + LINE2 + "  \n\n";
        service.applyTle(body);
        verify(orbitPropagationService).updateTle(eq("ISS (ZARYA)"), eq(LINE1), eq(LINE2));
    }

    @Test
    void skipsEmptyResponse() {
        service.applyTle("");
        verify(orbitPropagationService, never()).updateTle(any(), any(), any());
    }

    @Test
    void skipsNullResponse() {
        service.applyTle(null);
        verify(orbitPropagationService, never()).updateTle(any(), any(), any());
    }

    @Test
    void skipsResponseWithFewerThanTwoLines() {
        service.applyTle(LINE1);
        verify(orbitPropagationService, never()).updateTle(any(), any(), any());
    }

    @Test
    void swallowsPropagatorParseErrors() {
        // Orekit may reject malformed TLEs; service must keep running.
        doThrow(new RuntimeException("Orekit parse failure"))
                .when(orbitPropagationService).updateTle(any(), any(), any());
        service.applyTle("garbage line one\ngarbage line two");
        // No exception bubbles up — verified by reaching this assertion.
        verify(orbitPropagationService).updateTle(any(), any(), any());
    }

    @Test
    void httpFailureLogsAndDoesNotInvokePropagator() {
        final var spy = spy(service);
        doThrow(new RestClientException("simulated network error")).when(spy).fetchTleBody();
        spy.refreshTle();
        verify(orbitPropagationService, never()).updateTle(any(), any(), any());
    }
}
