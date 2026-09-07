// Copies maplibre-gl's worker bundle into public/ so it's served as a
// plain static file with a guaranteed-correct URL. maplibre-gl normally
// tries to auto-detect its own worker script URL at runtime (e.g. via
// document.currentScript), which resolves to an empty string when the
// library is loaded through a code-split dynamic import (as it is here,
// via next/dynamic) -- the worker then fails silently and every GeoJSON
// source/style hangs forever in a "loading" state. Explicitly pointing
// maplibregl.setWorkerUrl() at this static copy (see components/map/
// city-map.tsx) sidesteps that bundler-detection failure entirely.
const fs = require("fs");
const path = require("path");

const srcDir = path.join(__dirname, "..", "node_modules", "maplibre-gl", "dist");
const destDir = path.join(__dirname, "..", "public");

for (const file of [
  "maplibre-gl-worker.mjs",
  "maplibre-gl-worker.mjs.map",
  // The worker bundle imports this shared chunk via a relative specifier
  // resolved against wherever the worker script itself is served from.
  "maplibre-gl-shared.mjs",
  "maplibre-gl-shared.mjs.map",
]) {
  const src = path.join(srcDir, file);
  const dest = path.join(destDir, file);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`copied ${file} -> public/`);
  } else {
    console.warn(`WARNING: ${src} not found; maplibre-gl map layers may not render.`);
  }
}
