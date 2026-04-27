import { defineConfig } from "vite";
import { resolve } from "path";
import cesium from "vite-plugin-cesium";

// Multi-page Vite setup so /track.html and /commands.html each ship as
// independent operator views with their own JS entry. vite-plugin-cesium
// copies Cesium's static assets (Workers, Widgets, Assets) into dist/
// and sets CESIUM_BASE_URL so the runtime finds them.

export default defineConfig({
  plugins: [cesium()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        track: resolve(__dirname, "track.html"),
        commands: resolve(__dirname, "commands.html"),
      },
    },
  },
});
