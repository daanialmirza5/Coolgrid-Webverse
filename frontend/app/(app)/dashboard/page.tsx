"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowRight, Building2, Flame, Leaf, Thermometer, Users } from "lucide-react";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { useCity } from "@/lib/city-context";
import { useCityMapData } from "@/lib/use-city-map-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/ui/risk-badge";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { CityMap } from "@/components/map/city-map-loader";
import { MapLegend } from "@/components/map/map-legend";
import { formatNumber } from "@/lib/utils";

function StatTile({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between p-4">
        <div>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-1 text-2xl font-bold tabular-nums">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-400">
          <Icon className="h-4 w-4" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { city } = useCity();
  const router = useRouter();
  const summary = useApi(() => (city ? api.dashboard.summary(city.id) : Promise.reject(new Error("no city"))), [city?.id]);
  const hotspotsQuery = useApi(() => (city ? api.hotspots.list(city.id) : Promise.reject(new Error("no city"))), [city?.id]);
  const mapData = useCityMapData();

  if (!city || summary.loading) return <FullPageSpinner label="Loading dashboard..." />;
  if (summary.error) return <ErrorState message={summary.error} onRetry={summary.reload} />;
  if (!summary.data) return null;
  const s = summary.data;

  const topHotspots = (hotspotsQuery.data ?? []).slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">City Heat Overview</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">{s.city_name} · Updated {new Date(s.generated_at).toLocaleString()}</p>
        </div>
        {s.is_demo && <Badge variant="secondary">DEMO DATA — synthetic dataset, not real satellite observations</Badge>}
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile icon={Thermometer} label="Average LST" value={`${s.avg_lst}°C`} />
        <StatTile icon={Flame} label="Max LST" value={`${s.max_lst}°C`} />
        <StatTile icon={AlertTriangle} label="High/Critical Wards" value={String(s.hotspot_count)} />
        <StatTile icon={Users} label="Population Exposed" value={formatNumber(s.population_exposed)} />
        <StatTile icon={Leaf} label="Avg Vegetation" value={`${s.avg_vegetation_pct}%`} />
        <StatTile icon={Building2} label="Avg Built-up" value={`${s.avg_built_up_pct}%`} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Heat Map Preview</CardTitle>
            <Link href="/map">
              <Button variant="ghost" size="sm" className="gap-1">
                Open full map <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative h-80 w-full overflow-hidden rounded-b-xl">
              {mapData.data && city ? (
                <>
                  <CityMap data={mapData.data} activeLayer="heat" bbox={city.bbox} onSelectWard={(id) => router.push(`/hotspots/${id}`)} />
                  <div className="pointer-events-none absolute bottom-3 left-3 z-10">
                    <MapLegend activeLayer="heat" />
                  </div>
                </>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-400">Loading map…</div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Top Hotspots</CardTitle>
            <Link href="/hotspots">
              <Button variant="ghost" size="sm" className="gap-1">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {hotspotsQuery.loading && <p className="text-sm text-slate-400">Loading hotspots...</p>}
            {!hotspotsQuery.loading && topHotspots.length === 0 && (
              <p className="text-sm text-slate-400">No hotspots detected today.</p>
            )}
            {topHotspots.map((h) => (
              <button
                key={h.id}
                onClick={() => router.push(`/hotspots/${h.ward_id}`)}
                className="flex w-full items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
              >
                <div>
                  <p className="font-medium">{h.ward_name}</p>
                  <p className="text-xs text-slate-400">{h.lst_celsius}°C · score {h.heat_score}</p>
                </div>
                <RiskBadge risk={h.risk_level} />
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Suggested demo flow</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {[
            { href: "/map", label: "1. View heat map" },
            { href: "/hotspots", label: "2. Inspect hotspots" },
            { href: "/drivers", label: "3. Explain drivers" },
            { href: "/predictions", label: "4. See predictions" },
            { href: "/simulation", label: "5. Simulate interventions" },
            { href: "/optimization", label: "6. Optimize a plan" },
            { href: "/recommendations", label: "7. Read recommendations" },
            { href: "/reports", label: "8. Generate report" },
          ].map((step) => (
            <Link key={step.href} href={step.href}>
              <Button variant="outline" size="sm">
                {step.label}
              </Button>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
