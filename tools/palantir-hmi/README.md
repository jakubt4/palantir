# palantir-hmi

Browser-based operator HMI for Palantir — CesiumJS ground track (PAL-101) and a telecommand control panel (PAL-102), both backed by the Yamcs instance at `localhost:8090`.

## Quick start

Requires Node 20+ and the Palantir stack running (`docker compose up` from the repo root).

```bash
cd tools/palantir-hmi
cp .env.example .env.local
# Edit .env.local and paste a free token from https://cesium.com/ion/tokens

npm install
npm start
```

Open the printed URL (default `http://localhost:5173/`). The landing page links to `/track.html` (PAL-101) and `/commands.html` (PAL-102).

## Pages

| Path | Ticket | Status |
|---|---|---|
| `/` | — | landing page with navigation |
| `/track.html` | PAL-101 | scaffold (impl in next commit) |
| `/commands.html` | PAL-102 | scaffold (impl after PAL-101) |

## Architecture

Two-page Vite app sharing styles and (later) Yamcs WebSocket / REST client modules under `src/`. `vite-plugin-cesium` handles Cesium's static asset copying and `CESIUM_BASE_URL` setup so the runtime workers, widgets, and assets resolve correctly in both dev and build.

CORS against Yamcs is permitted via `allowOrigin: "*"` already set in `yamcs/etc/yamcs.yaml`, so the browser hits Yamcs directly without a proxy.

## Cesium Ion token

The free Community Ion tier covers exploratory development and non-commercial personal projects (current PoC status). When the project moves to paying customers or government/funded research, the token must be upgraded **or** the imagery provider switched away from Ion (e.g. `OpenStreetMapImageryProvider`).
