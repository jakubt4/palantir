package io.github.jakubt4.palantir.controller;

import io.github.jakubt4.palantir.service.OrbitPropagationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TleIngestionController.class)
class TleIngestionControllerTest {

    private static final String TLE_LINE1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927";
    private static final String TLE_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537";

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrbitPropagationService orbitPropagationService;

    @Test
    void ingestTleReturnsActiveStatusForValidPayload() throws Exception {
        mockMvc.perform(post("/api/orbit/tle")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                    "satelliteName": "ISS (ZARYA)",
                                    "line1": "%s",
                                    "line2": "%s"
                                }
                                """.formatted(TLE_LINE1, TLE_LINE2)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.satelliteName").value("ISS (ZARYA)"))
                .andExpect(jsonPath("$.status").value("ACTIVE"));

        verify(orbitPropagationService).updateTle("ISS (ZARYA)", TLE_LINE1, TLE_LINE2);
    }

    @Test
    void ingestTleReturnsBadRequestForBlankSatelliteName() throws Exception {
        mockMvc.perform(post("/api/orbit/tle")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                    "satelliteName": "",
                                    "line1": "%s",
                                    "line2": "%s"
                                }
                                """.formatted(TLE_LINE1, TLE_LINE2)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value("REJECTED"));
    }

    @Test
    void ingestTleReturnsBadRequestForInvalidTle() throws Exception {
        doThrow(new RuntimeException("TLE line 1 too short"))
                .when(orbitPropagationService).updateTle(anyString(), anyString(), anyString());

        mockMvc.perform(post("/api/orbit/tle")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                    "satelliteName": "BAD-SAT",
                                    "line1": "invalid",
                                    "line2": "invalid"
                                }
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value("REJECTED"))
                .andExpect(jsonPath("$.message").value(org.hamcrest.Matchers.containsString("Invalid TLE")));
    }
}
