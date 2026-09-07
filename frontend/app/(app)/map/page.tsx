"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useCityMapData } from "@/lib/use-city-map-data";
import { CityMap } from "@/components/map/city-map-loader";
import { MapLegend } from "@/components/map/map-legend";
import { LAYER_LABELS, type MapLayerKey } from "@/lib/map-utils";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const LAYERS: MapLayerKey[] = ["heat", "risk", "vegetation", "built_up", "population"];

export default function MapPage() {
  const router = useRouter();
  const { city, data, hotspots, loading, error, reload } = useCityMapData();
  const [activeLayer, setActiveLayer] = useState<MapLayerKey>("heat");
  const [selectedWardId, setSelectedWardId] = useState<string | null>(null);

  if (loading) return <FullPageSpinner label="Loading heat map..." />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data || !city) return null;

  const selected = hotspots?.find((h) => h.ward_id === selectedWardId);

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-bold">Heat Map</h1>
        <div className="flex flex-wrap gap-1.5">
          {LAYERS.map((layer) => (
            <button
              key={layer}
              onClick={() => setActiveLayer(layer)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                activeLayer === layer
                  ? "border-sky-700 bg-sky-700 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              )}
            >
              {LAYER_LABELS[layer]}
            </button>
          ))}
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
        <CityMap
          data={data}
          activeLayer={activeLayer}
          bbox={city.bbox}
          selectedWardId={selectedWardId}
          onSelectWard={setSelectedWardId}
        />
        {/* MapLibre's canvas can otherwise paint over sibling overlays regardless
            of DOM order -- an explicit z-index is required, not optional. */}
        <div className="pointer-events-none absolute bottom-4 left-4 z-10">
          <MapLegend activeLayer={activeLayer} />
        </div>

        {selected && (
          <div className="absolute right-4 top-4 z-10 w-72">
            <Card>
              <CardContent className="space-y-2 p-4">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{selected.ward_name}</p>
                  <RiskBadge risk={selected.risk_level} />
                </div>
                <p className="text-sm text-slate-500">
                  LST {selected.lst_celsius}°C (range {selected.lst_lower}–{selected.lst_upper}°C)
                </p>
                <p className="text-xs text-slate-400">Heat score {selected.heat_score}/100 · Confidence {(selected.confidence * 100).toFixed(0)}%</p>
                <Button size="sm" className="w-full" onClick={() => router.push(`/hotspots/${selected.ward_id}`)}>
                  View hotspot details
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
