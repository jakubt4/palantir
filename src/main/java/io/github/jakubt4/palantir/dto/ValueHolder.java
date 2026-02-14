package io.github.jakubt4.palantir.dto;

public record ValueHolder(String type, float floatValue) {

    public static ValueHolder ofFloat(double value) {
        return new ValueHolder("FLOAT", (float) value);
    }
}
