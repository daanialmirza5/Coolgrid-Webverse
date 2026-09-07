"use client";

import { useMemo } from "react";
import { api } from "./api-client";
import { useApi } from "./use-api";
import { enrichWardGeoJSON } from "./map-utils";
import { useCity } from "./city-context";

export function useCityMapData() {
  const { city } = useCity();
  const geoJson = useApi(() => (city ? api.cities.wardsGeoJSON(city.id) : Promise.reject(new Error("no city"))), [city?.id]);
  const hotspots = useApi(() => (city ? api.hotspots.list(city.id) : Promise.reject(new Error("no city"))), [city?.id]);

  const enriched = useMemo(() => {
    if (!geoJson.data || !hotspots.data) return null;
    return enrichWardGeoJSON(geoJson.data, hotspots.data);
  }, [geoJson.data, hotspots.data]);

  return {
    city,
    data: enriched,
    hotspots: hotspots.data,
    loading: geoJson.loading || hotspots.loading,
    error: geoJson.error || hotspots.error,
    reload: () => {
      geoJson.reload();
      hotspots.reload();
    },
  };
}
