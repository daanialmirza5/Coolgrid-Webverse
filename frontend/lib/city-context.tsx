"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api-client";
import type { City } from "./types";

interface CityContextValue {
  city: City | null;
  loading: boolean;
  error: string | null;
}

const CityContext = createContext<CityContextValue>({ city: null, loading: true, error: null });

/** CoolGrid's demo deployment has exactly one city; this loads it once and
 * shares it app-wide so every page doesn't need to re-fetch the city list. */
export function CityProvider({ children }: { children: React.ReactNode }) {
  const [city, setCity] = useState<City | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.cities
      .list()
      .then((cities) => setCity(cities[0] ?? null))
      .catch(() => setError("Could not load city data. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  return <CityContext.Provider value={{ city, loading, error }}>{children}</CityContext.Provider>;
}

export function useCity() {
  return useContext(CityContext);
}
