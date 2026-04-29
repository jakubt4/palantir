package io.github.jakubt4.palantir.dto;

/**
 * Inbound request for TLE ingestion via the REST API.
 *
 * @param satelliteName human-readable satellite identifier (e.g. "ISS (ZARYA)")
 * @param line1         first line of the NORAD two-line element set
 * @param line2         second line of the NORAD two-line element set
 */
public record TleRequest(String satelliteName, String line1, String line2) {
}
