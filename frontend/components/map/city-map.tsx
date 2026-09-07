"use client";

import { useEffect, useRef, useState } from "react";
import { Map as MLMap, NavigationControl, Popup, setWorkerUrl, type GeoJSONSource, type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection, Geometry, GeoJsonProperties } from "geojson";
import type { EnrichedWardGeoJSON, MapLayerKey } from "@/lib/map-utils";
import { LAYER_FILL_PROPERTY } from "@/lib/map-utils";

const SOURCE_ID = "wards";
const FILL_LAYER_ID = "wards-fill";
const LINE_LAYER_ID = "wards-outline";
const SELECTED_LAYER_ID = "wards-selected";

// A fully self-contained style (no remote tiles, no external style JSON) so
// the map never depends on a third-party basemap host being reachable --
// per the product spec's own requirement that CoolGrid "must not depend on
// fragile external APIs." Ward polygons, colors, borders, tooltips and the
// legend carry all the information city planners need; a detailed street
// basemap isn't required for a ward-level heat choropleth.
//
// The background/outline colors are read once at mount from the OS color
// scheme (there's no in-app theme toggle to react to) -- without this, a
// dark-mode viewer gets a jarring bright rectangle where the map sits, and
// the ward outline (dark-on-dark) becomes invisible.
function prefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches;
}

function blankStyle(isDark: boolean): StyleSpecification {
  return {
    version: 8,
    sources: {},
    layers: [{ id: "background", type: "background", paint: { "background-color": isDark ? "#1e293b" : "#eef2f6" } }],
  };
}

// See scripts/copy-maplibre-worker.js for why this is necessary: maplibre-gl's
// automatic worker-URL detection resolves to an empty string when the library
// is loaded via a code-split dynamic import, silently breaking every source.
if (typeof window !== "undefined") {
  setWorkerUrl("/maplibre-gl-worker.mjs");
}

interface CityMapProps {
  data: EnrichedWardGeoJSON;
  activeLayer: MapLayerKey;
  bbox: [number, number, number, number];
  selectedWardId?: string | null;
  onSelectWard?: (wardId: string) => void;
  className?: string;
}

export function CityMap({ data, activeLayer, bbox, selectedWardId, onSelectWard, className }: CityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const popupRef = useRef<Popup | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Initialize map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const isDark = prefersDark();
    const map = new MLMap({
      container: containerRef.current,
      style: blankStyle(isDark),
      bounds: [
        [bbox[0], bbox[1]],
        [bbox[2], bbox[3]],
      ],
      fitBoundsOptions: { padding: 20 },
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    popupRef.current = new Popup({ closeButton: false, closeOnClick: false });

    map.on("load", () => {
      map.addSource(SOURCE_ID, { type: "geojson", data: data as FeatureCollection<Geometry, GeoJsonProperties> });
      map.addLayer({
        id: FILL_LAYER_ID,
        type: "fill",
        source: SOURCE_ID,
        paint: { "fill-color": ["get", LAYER_FILL_PROPERTY[activeLayer]], "fill-opacity": 0.75 },
      });
      map.addLayer({
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        paint: { "line-color": isDark ? "#94a3b8" : "#1e293b", "line-width": 0.6, "line-opacity": 0.4 },
      });
      map.addLayer({
        id: SELECTED_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        paint: { "line-color": "#0369a1", "line-width": 3 },
        filter: ["==", ["get", "id"], selectedWardId ?? "__none__"],
      });

      map.on("mousemove", FILL_LAYER_ID, (e) => {
        map.getCanvas().style.cursor = "pointer";
        const f = e.features?.[0];
        if (!f || !popupRef.current) return;
        const p = f.properties as Record<string, unknown>;
        const lstTxt = p.lst_celsius != null ? `${Number(p.lst_celsius).toFixed(1)}°C` : "N/A";
        // MapLibre's default popup chrome is white-on-dark-text regardless of
        // page theme; override both the wrapper (via a `!important`-free style
        // attribute MapLibre applies to `.maplibregl-popup-content`) and the
        // inner text color so it doesn't look like a stray light box in dark mode.
        popupRef.current
          .setLngLat(e.lngLat)
          .setHTML(
            `<div style="font:12px system-ui;min-width:140px;background:${isDark ? "#1e293b" : "#ffffff"};color:${isDark ? "#e2e8f0" : "#0f172a"};margin:-10px;padding:10px;border-radius:6px">
              <strong>${p.name}</strong><br/>
              LST: ${lstTxt} · Risk: ${p.risk_level ?? "N/A"}<br/>
              Vegetation: ${Number(p.green_space_pct).toFixed(0)}% · Built-up: ${(Number(p.built_up_density) * 100).toFixed(0)}%
            </div>`
          )
          .addTo(map);
      });
      map.on("mouseleave", FILL_LAYER_ID, () => {
        map.getCanvas().style.cursor = "";
        popupRef.current?.remove();
      });
      map.on("click", FILL_LAYER_ID, (e) => {
        const f = e.features?.[0];
        const id = f?.properties?.id as string | undefined;
        if (id && onSelectWard) onSelectWard(id);
      });

      setLoaded(true);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update data when it changes.
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const source = mapRef.current.getSource(SOURCE_ID) as GeoJSONSource | undefined;
    source?.setData(data as FeatureCollection<Geometry, GeoJsonProperties>);
  }, [data, loaded]);

  // Update active layer paint property.
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    mapRef.current.setPaintProperty(FILL_LAYER_ID, "fill-color", ["get", LAYER_FILL_PROPERTY[activeLayer]]);
  }, [activeLayer, loaded]);

  // Update selection highlight.
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    mapRef.current.setFilter(SELECTED_LAYER_ID, ["==", ["get", "id"], selectedWardId ?? "__none__"]);
  }, [selectedWardId, loaded]);

  return <div ref={containerRef} className={className ?? "h-full w-full"} />;
}
