package io.github.jakubt4.palantir.dto;

public record ParameterValue(Id id, ValueHolder value) {

    public record Id(String name) {}

    public static ParameterValue of(String name, double val) {
        return new ParameterValue(new Id(name), ValueHolder.ofFloat(val));
    }
}
