package io.github.jakubt4.palantir.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class YamcsParameterRequestTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void serializesToExpectedJsonShape() throws Exception {
        final var request = new YamcsParameterRequest(List.of(
                ParameterValue.of("/Palantir/Latitude", 51.5)
        ));

        final var json = objectMapper.writeValueAsString(request);

        final var tree = objectMapper.readTree(json);
        final var requestArray = tree.get("request");
        assertThat(requestArray.isArray()).isTrue();
        assertThat(requestArray).hasSize(1);

        final var param = requestArray.get(0);
        assertThat(param.get("id").get("name").asText()).isEqualTo("/Palantir/Latitude");
        assertThat(param.get("value").get("type").asText()).isEqualTo("FLOAT");
        assertThat(param.get("value").get("floatValue").floatValue()).isEqualTo(51.5f);
    }

    @Test
    void valueHolderOfFloatConvertsDoubleToFloat() {
        final var holder = ValueHolder.ofFloat(3.14159265);

        assertThat(holder.type()).isEqualTo("FLOAT");
        assertThat(holder.floatValue()).isEqualTo((float) 3.14159265);
    }
}
