"use client";

import dynamic from "next/dynamic";
import { Spinner } from "@/components/ui/spinner";

// maplibre-gl touches `window` at module load time, so it must never be
// part of the server-rendered/prerendered bundle for a client component.
export const CityMap = dynamic(() => import("./city-map").then((m) => m.CityMap), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-slate-100 dark:bg-slate-800">
      <Spinner />
    </div>
  ),
});
