/**
 * PAL-101 — Real-time orbital ground track on a Cesium globe.
 *
 * Subscribes to /Palantir/{Latitude,Longitude,Altitude} via Yamcs
 * WebSocket and renders the spacecraft position as a moving point with
 * a trailing polyline showing one full orbital period of history.
 *
 * Critical unit boundary: Yamcs Altitude is in **kilometres** (XTCE
 * UnitSet), CesiumJS Cartesian3.fromDegrees expects **metres**. The
 * `* 1000.0` multiply on line `metersFromKm` is the single most common
 * Cesium ground-track bug — keeping it explicit and named.
 */

import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

import { subscribeParameters } from "./yamcs-ws.js";

const ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
const YAMCS_WS_URL = "ws://localhost:8090/api/websocket";
const INSTANCE = "palantir";
const PROCESSOR = "realtime";

// Trail length: one ISS-class orbit ≈ 5554 s. Round to 93 min (5580 s)
// per FEATURES.md §1.1; 1 Hz cadence gives 5580 stored samples max.
const TRAIL_SECONDS = 93 * 60;

if (ION_TOKEN) {
  Cesium.Ion.defaultAccessToken = ION_TOKEN;
} else {
  // Fallback when the dev forgot to copy .env.example to .env.local.
  // The default Bing imagery won't load without an Ion token, so swap
  // to OSM so the globe still has texture.
  console.warn("VITE_CESIUM_ION_TOKEN missing — falling back to OSM imagery.");
}

const viewer = new Cesium.Viewer("cesiumContainer", {
  imageryProvider: ION_TOKEN
    ? undefined  // Ion default (Bing Maps satellite)
    : new Cesium.OpenStreetMapImageryProvider({ url: "https://tile.openstreetmap.org/" }),
  terrainProvider: new Cesium.EllipsoidTerrainProvider(),  // smooth ellipsoid; fine for ground track
  baseLayerPicker: false,
  geocoder: false,
  homeButton: false,
  navigationHelpButton: false,
  sceneModePicker: false,
  timeline: false,
  animation: false,
  fullscreenButton: false,
  selectionIndicator: false,
  infoBox: false,
});
viewer.scene.globe.enableLighting = true;

// Spacecraft entity — point + label. SampledPositionProperty interpolates
// smoothly between 1 Hz telemetry ticks; HOLD extrapolation prevents the
// icon flying off into the future when the WS drops.
const positionProperty = new Cesium.SampledPositionProperty();
positionProperty.forwardExtrapolationType = Cesium.ExtrapolationType.HOLD;
positionProperty.backwardExtrapolationType = Cesium.ExtrapolationType.HOLD;

viewer.entities.add({
  id: "palantir-spacecraft",
  position: positionProperty,
  point: {
    pixelSize: 12,
    color: Cesium.Color.YELLOW,
    outlineColor: Cesium.Color.BLACK,
    outlineWidth: 2,
  },
  label: {
    text: "PALANTIR",
    font: "13px sans-serif",
    fillColor: Cesium.Color.WHITE,
    outlineColor: Cesium.Color.BLACK,
    outlineWidth: 2,
    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
    pixelOffset: new Cesium.Cartesian2(0, -22),
  },
});

// Trailing polyline — array of (time, Cartesian3) pairs, trimmed to TRAIL_SECONDS.
const trailSamples = [];
const trailPositions = new Cesium.CallbackProperty(() => trailSamples.map((s) => s.cart), false);
viewer.entities.add({
  polyline: {
    positions: trailPositions,
    width: 2,
    material: Cesium.Color.CYAN.withAlpha(0.7),
    clampToGround: false,
  },
});

// Live telemetry buffer — last value for each parameter.
const latest = { lat: undefined, lon: undefined, alt_km: undefined, time: undefined };
const altitudeReadout = document.getElementById("altitudeReadout");
const statusReadout = document.getElementById("statusReadout");

function maybePushSample() {
  const { lat, lon, alt_km, time } = latest;
  if (lat === undefined || lon === undefined || alt_km === undefined) return;

  const metersFromKm = alt_km * 1000.0;  // ← The km→m boundary fix.
  const cart = Cesium.Cartesian3.fromDegrees(lon, lat, metersFromKm);
  const julian = Cesium.JulianDate.fromDate(time);

  positionProperty.addSample(julian, cart);
  trailSamples.push({ julian, cart });

  // Trim trail to last TRAIL_SECONDS.
  const cutoff = Cesium.JulianDate.addSeconds(julian, -TRAIL_SECONDS, new Cesium.JulianDate());
  while (trailSamples.length > 0 &&
         Cesium.JulianDate.lessThan(trailSamples[0].julian, cutoff)) {
    trailSamples.shift();
  }

  altitudeReadout.textContent = `${alt_km.toFixed(2)} km`;

  // Drive Cesium's clock so smooth interpolation works against wall time.
  viewer.clock.currentTime = julian;
}

subscribeParameters(
  YAMCS_WS_URL,
  INSTANCE,
  PROCESSOR,
  ["/Palantir/Latitude", "/Palantir/Longitude", "/Palantir/Altitude"],
  ({ name, value, time }) => {
    latest.time = time;
    if (name.endsWith("/Latitude")) latest.lat = value;
    else if (name.endsWith("/Longitude")) latest.lon = value;
    else if (name.endsWith("/Altitude")) latest.alt_km = value;
    maybePushSample();
  },
  (state) => {
    statusReadout.textContent = state;
    statusReadout.className = `status status-${state}`;
  },
);
