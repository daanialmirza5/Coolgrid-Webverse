"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { useCity } from "@/lib/city-context";
import { Card, CardContent } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState, EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/types";
import { Flame } from "lucide-react";

const RISK_FILTERS: Array<RiskLevel | "ALL"> = ["ALL", "CRITICAL", "HIGH", "MODERATE", "LOW"];

export default function HotspotsPage() {
  const { city } = useCity();
  const router = useRouter();
  const [filter, setFilter] = useState<RiskLevel | "ALL">("ALL");
  const hotspots = useApi(
    () => (city ? api.hotspots.list(city.id, filter === "ALL" ? undefined : filter) : Promise.reject(new Error("no city"))),
    [city?.id, filter]
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold">Hotspots</h1>
        <div className="flex gap-1.5">
          {RISK_FILTERS.map((r) => (
            <button
              key={r}
              onClick={() => setFilter(r)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium",
                filter === r
                  ? "border-sky-700 bg-sky-700 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {hotspots.loading && <FullPageSpinner />}
      {hotspots.error && <ErrorState message={hotspots.error} onRetry={hotspots.reload} />}
      {hotspots.data && hotspots.data.length === 0 && (
        <EmptyState icon={Flame} title="No hotspots match this filter" description="Try a different risk level." />
      )}

      {hotspots.data && hotspots.data.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {hotspots.data.map((h) => (
            <Card
              key={h.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => router.push(`/hotspots/${h.ward_id}`)}
            >
              <CardContent className="space-y-2 p-4">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">
                    #{h.rank_in_city} · {h.ward_name}
                  </p>
                  <RiskBadge risk={h.risk_level} />
                </div>
                <p className="text-2xl font-bold tabular-nums">{h.lst_celsius}°C</p>
                <p className="text-xs text-slate-500">
                  Range {h.lst_lower}–{h.lst_upper}°C · Heat score {h.heat_score}/100
                </p>
                <p className="text-xs text-slate-400">Confidence {(h.confidence * 100).toFixed(0)}%</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
