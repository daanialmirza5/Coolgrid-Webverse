"use client";

import { useParams, useRouter } from "next/navigation";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/ui/risk-badge";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { CHART } from "@/lib/colors";
import { formatNumber } from "@/lib/utils";
import { ArrowLeft, FlaskConical, Lightbulb, TrendingUp } from "lucide-react";

export default function HotspotDetailPage() {
  const params = useParams<{ wardId: string }>();
  const wardId = params.wardId;
  const router = useRouter();

  const ward = useApi(() => api.wards.get(wardId), [wardId]);
  const hotspot = useApi(() => api.hotspots.forWard(wardId), [wardId]);
  const drivers = useApi(() => api.drivers.forWard(wardId), [wardId]);

  if (ward.loading || hotspot.loading) return <FullPageSpinner label="Loading ward details..." />;
  if (ward.error) return <ErrorState message={ward.error} onRetry={ward.reload} />;
  if (!ward.data) return null;

  const w = ward.data;
  const h = hotspot.data;
  const topDrivers = (drivers.data?.drivers ?? []).slice(0, 5);

  return (
    <div className="space-y-6">
      <button onClick={() => router.push("/hotspots")} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
        <ArrowLeft className="h-4 w-4" /> Back to hotspots
      </button>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">{w.name}</h1>
          <p className="text-sm capitalize text-slate-500 dark:text-slate-400">{w.archetype.replace(/_/g, " ")} ward</p>
        </div>
        {h && <RiskBadge risk={h.risk_level} className="text-sm" />}
      </div>

      {!h ? (
        <ErrorState message="No hotspot record yet for this ward." />
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">Current LST</p>
              <p className="text-2xl font-bold tabular-nums">{h.lst_celsius}°C</p>
              <p className="text-xs text-slate-400">Range {h.lst_lower}–{h.lst_upper}°C</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">Heat Score</p>
              <p className="text-2xl font-bold tabular-nums">{h.heat_score}/100</p>
              <p className="text-xs text-slate-400">City rank #{h.rank_in_city}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">Confidence</p>
              <p className="text-2xl font-bold tabular-nums">{(h.confidence * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">Population</p>
              <p className="text-2xl font-bold tabular-nums">{formatNumber(w.population_total)}</p>
              <p className="text-xs text-slate-400">{w.vulnerable_population_pct}% vulnerable</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top heat drivers</CardTitle>
            <CardDescription>{drivers.data?.narrative}</CardDescription>
          </CardHeader>
          <CardContent>
            {drivers.loading ? (
              <FullPageSpinner />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={topDrivers} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid horizontal={false} stroke={CHART.grid} />
                  <XAxis type="number" tick={{ fontSize: 11 }} unit="%" stroke={CHART.axis} />
                  <YAxis dataKey="label" type="category" width={190} tick={{ fontSize: 11 }} stroke={CHART.axis} />
                  <Tooltip formatter={(v) => `${Number(v)}%`} />
                  <Bar dataKey="relative_contribution_pct" radius={[0, 4, 4, 0]}>
                    {topDrivers.map((d, i) => (
                      <Cell key={i} fill={d.direction === "increases_heat" ? CHART.warms : CHART.cools} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
            <Button variant="link" size="sm" onClick={() => router.push(`/drivers?ward=${wardId}`)}>
              Full driver analysis →
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ward profile</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <Profile label="Area" value={`${w.area_km2} km²`} />
            <Profile label="Built-up density" value={`${(w.built_up_density * 100).toFixed(0)}%`} />
            <Profile label="Vegetation" value={`${w.green_space_pct}%`} />
            <Profile label="Water bodies" value={`${w.water_body_pct}%`} />
            <Profile label="Road density" value={`${w.road_density_km_per_km2} km/km²`} />
            <Profile label="Avg building height" value={`${w.building_height_mean_m} m`} />
            <Profile label="Surface albedo" value={w.albedo_base.toFixed(2)} />
            <Profile label="Population density" value={`${formatNumber(w.population_density_per_km2)}/km²`} />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant="outline" className="gap-2" onClick={() => router.push(`/drivers?ward=${wardId}`)}>
          <Lightbulb className="h-4 w-4" /> Driver analysis
        </Button>
        <Button variant="outline" className="gap-2" onClick={() => router.push(`/predictions?ward=${wardId}`)}>
          <TrendingUp className="h-4 w-4" /> View predictions
        </Button>
        <Button className="gap-2" onClick={() => router.push(`/simulation?ward=${wardId}`)}>
          <FlaskConical className="h-4 w-4" /> Simulate interventions
        </Button>
      </div>
    </div>
  );
}

function Profile({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
