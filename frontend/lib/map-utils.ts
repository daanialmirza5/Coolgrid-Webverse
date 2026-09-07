import { heatColor, RISK_COLOR } from "./colors";
import type { Hotspot, RiskLevel, WardGeoJSON } from "./types";

export type MapLayerKey = "heat" | "risk" | "vegetation" | "built_up" | "population";

export interface EnrichedWardProperties {
  id: string;
  ward_code: string;
  name: string;
  archetype: string;
  built_up_density: number;
  green_space_pct: number;
  water_body_pct: number;
  population_total: number;
  lst_celsius: number | null;
  heat_score: number | null;
  risk_level: RiskLevel | null;
  fill_heat: string;
  fill_risk: string;
  fill_vegetation: string;
  fill_built_up: string;
  fill_population: string;
}

export type EnrichedWardGeoJSON = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: WardGeoJSON["features"][number]["geometry"];
    properties: EnrichedWardProperties;
  }>;
};

function vegetationColor(pct: number): string {
  // 0-70% green cover -> pale to deep green (single-hue sequential).
  const t = Math.max(0, Math.min(1, pct / 70));
  const from = [241, 245, 233];
  const to = [22, 101, 52];
  const c = from.map((v, i) => Math.round(v + (to[i] - v) * t));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function builtUpColor(density: number): string {
  const t = Math.max(0, Math.min(1, density));
  const from = [241, 245, 249];
  const to = [51, 65, 85];
  const c = from.map((v, i) => Math.round(v + (to[i] - v) * t));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function populationColor(pop: number, maxPop: number): string {
  const t = maxPop > 0 ? Math.max(0, Math.min(1, pop / maxPop)) : 0;
  const from = [237, 233, 254];
  const to = [76, 29, 149];
  const c = from.map((v, i) => Math.round(v + (to[i] - v) * t));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

/** Joins live hotspot detection results into the static ward GeoJSON and
 * precomputes a fill color per layer, so the map component just reads a
 * property instead of running MapLibre data-driven expressions. */
export function enrichWardGeoJSON(base: WardGeoJSON, hotspots: Hotspot[]): EnrichedWardGeoJSON {
  const byWardId = new Map(hotspots.map((h) => [h.ward_id, h]));
  const maxPop = Math.max(1, ...base.features.map((f) => f.properties.population_total));

  return {
    type: "FeatureCollection",
    features: base.features.map((f) => {
      const hotspot = byWardId.get(f.properties.id);
      return {
        type: "Feature",
        geometry: f.geometry,
        properties: {
          ...f.properties,
          lst_celsius: hotspot?.lst_celsius ?? null,
          heat_score: hotspot?.heat_score ?? null,
          risk_level: hotspot?.risk_level ?? null,
          fill_heat: hotspot ? heatColor(hotspot.heat_score) : "#cbd5e1",
          fill_risk: hotspot ? RISK_COLOR[hotspot.risk_level] : "#cbd5e1",
          fill_vegetation: vegetationColor(f.properties.green_space_pct),
          fill_built_up: builtUpColor(f.properties.built_up_density),
          fill_population: populationColor(f.properties.population_total, maxPop),
        },
      };
    }),
  };
}

export const LAYER_FILL_PROPERTY: Record<MapLayerKey, string> = {
  heat: "fill_heat",
  risk: "fill_risk",
  vegetation: "fill_vegetation",
  built_up: "fill_built_up",
  population: "fill_population",
};

export const LAYER_LABELS: Record<MapLayerKey, string> = {
  heat: "Land Surface Temperature",
  risk: "Heat Risk Level",
  vegetation: "Vegetation Cover",
  built_up: "Built-up Density",
  population: "Population",
};
