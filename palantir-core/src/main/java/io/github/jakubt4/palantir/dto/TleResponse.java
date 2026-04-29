package io.github.jakubt4.palantir.dto;

/**
 * Response returned after a TLE ingestion attempt.
 *
 * @param satelliteName satellite the TLE was submitted for (may be {@code null} on early rejection)
 * @param status        outcome — {@code "ACTIVE"} if propagation started, {@code "REJECTED"} otherwise
 * @param message       human-readable detail about the result
 */
public record TleResponse(String satelliteName, String status, String message) {
}
