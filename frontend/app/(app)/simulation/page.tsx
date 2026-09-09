"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from "recharts";
import { api, ApiError } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { WardPicker } from "@/components/ward-picker";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { RiskBadge } from "@/components/ui/risk-badge";
import { CHART, heatColor } from "@/lib/colors";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { InterventionType, SimulationResult } from "@/lib/types";
import { FlaskConical, TrendingDown, DollarSign, Droplets, Users, ShieldCheck } from "lucide-react";

function SimulationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Simulation" description="Select a ward to test cooling interventions." onSelect={(id) => router.push(`/simulation?ward=${id}`)} />;
  }
  return <SimulationForWard wardId={wardId} onChangeWard={() => router.push("/simulation")} />;
}

interface SimulationPreset {
  id: string;
  name: string;
  tagline: string;
  description: string;
  icon: string;
  badge: string;
  coverage: Record<string, number>;
}

const SIMULATION_PRESETS: SimulationPreset[] = [
  {
    id: "cool-roof-program",
    name: "Reflective Cool Roofs",
    tagline: "High Albedo / Fast Deploy",
    description: "Converts 60% of eligible rooftops to high-albedo cool coatings with 20% reflective pavement. Zero land or water requirement.",
    icon: "🏠",
    badge: "Zero Water",
    coverage: { cool_roofs: 60, reflective_surfaces: 20 },
  },
  {
    id: "urban-canopy-expansion",
    name: "Urban Canopy & Corridors",
    tagline: "Biophilic Evapotranspiration",
    description: "Deploys 30% urban street trees, 15% linear vegetation corridors, and 5% blue infrastructure for maximum biological shade and microclimate cooling.",
    icon: "🌳",
    badge: "Biophilic",
    coverage: { urban_trees: 30, vegetation_corridors: 15, blue_infrastructure: 5 },
  },
  {
    id: "high-density-mitigation",
    name: "Commercial Core Retrofit",
    tagline: "Balanced Multi-Layer Strategy",
    description: "Tailored for dense urban wards: 40% cool roofs, 25% green roofs, 15% street trees, and 20% high-albedo pavements.",
    icon: "🏙️",
    badge: "High-Density",
    coverage: { cool_roofs: 40, green_roofs: 25, urban_trees: 15, reflective_surfaces: 20 },
  },
  {
    id: "heatwave-resilience",
    name: "Emergency Heatwave Shield",
    tagline: "Aggressive Hotspot Suppression",
    description: "Emergency package targeting extreme LST: 65% cool roofs, 45% reflective pavements, 25% trees, and 10% evaporative water bodies.",
    icon: "🔥",
    badge: "Maximum Cooling",
    coverage: { cool_roofs: 65, reflective_surfaces: 45, urban_trees: 25, blue_infrastructure: 10 },
  },
  {
    id: "zero-water-conservation",
    name: "Arid Passive Albedo",
    tagline: "100% Water-Neutral Mitigation",
    description: "Strictly water-neutral passive cooling: 75% high-reflectance roof coatings and 50% albedo road treatments for drought-sensitive zones.",
    icon: "💧",
    badge: "Arid Resilient",
    coverage: { cool_roofs: 75, reflective_surfaces: 50 },
  },
];

function SimulationForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const catalog = useApi(() => api.interventions.catalog(), []);
  const ward = useApi(() => api.wards.get(wardId), [wardId]);
  const [coverage, setCoverage] = useState<Record<string, number>>({});
  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (catalog.loading || ward.loading) return <FullPageSpinner label="Loading intervention catalog..." />;
  if (catalog.error) return <ErrorState message={catalog.error} onRetry={catalog.reload} />;
  if (!catalog.data || !ward.data) return null;

  function applyPreset(preset: SimulationPreset) {
    setActivePreset(preset.id);
    const newCoverage: Record<string, number> = {};
    for (const [key, val] of Object.entries(preset.coverage)) {
      newCoverage[key] = val;
    }
    setCoverage(newCoverage);
    setError(null);
  }

  async function runSimulation() {
    const interventions = Object.entries(coverage)
      .filter(([, v]) => v > 0)
      .map(([type, coverage_pct]) => ({ type: type as InterventionType, coverage_pct }));
    if (interventions.length === 0) {
      setError("Set at least one intervention above 0% coverage or pick a preset above.");
      return;
    }
    setError(null);
    setRunning(true);
    try {
      const res = await api.simulations.run(wardId, interventions);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Simulation failed");
    } finally {
      setRunning(false);
    }
  }

  const beforeAfterData = result
    ? [
        { label: "Baseline LST", value: result.baseline_lst },
        { label: "Simulated Post-Intervention", value: result.simulated_lst },
      ]
    : [];

  // Derived comparative metrics
  const costPerTenthDegree = result && result.expected_cooling_c > 0
    ? result.cost_usd / (result.expected_cooling_c * 10)
    : 0;

  const waterPerDegree = result && result.expected_cooling_c > 0
    ? result.water_m3_per_year / result.expected_cooling_c
    : 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Simulate Interventions — {ward.data.name}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Choose an urban scenario preset or configure custom coverage for physics-based cooling simulation.</p>
        </div>
        <Button variant="outline" size="sm" onClick={onChangeWard}>
          Change ward
        </Button>
      </div>

      {/* Interactive Scenario Presets */}
      <Card className="border-emerald-200/50 bg-slate-50/50 dark:border-emerald-900/30 dark:bg-slate-900/30">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <span>🎯</span> Interactive Scenario Presets (Zero-Config Testing)
              </CardTitle>
              <CardDescription className="text-xs">
                Select an urban climate intervention package to automatically configure parameters across the physics engine.
              </CardDescription>
            </div>
            {activePreset && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-slate-500"
                onClick={() => {
                  setActivePreset(null);
                  setCoverage({});
                }}
              >
                Reset to Custom
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-5">
            {SIMULATION_PRESETS.map((p) => {
              const isSelected = activePreset === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className={`flex flex-col justify-between rounded-lg border p-3 text-left transition-all ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-50/70 shadow-sm dark:border-emerald-400 dark:bg-emerald-950/40"
                      : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-lg">{p.icon}</span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                          isSelected
                            ? "bg-emerald-200 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {p.badge}
                      </span>
                    </div>
                    <div className="font-semibold text-xs text-slate-900 dark:text-slate-100">{p.name}</div>
                    <div className="text-[11px] text-slate-500 line-clamp-2">{p.description}</div>
                  </div>
                  <div className="mt-2 text-[10px] font-medium text-emerald-700 dark:text-emerald-400">
                    {isSelected ? "✓ Active Preset" : "Apply Preset →"}
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Intervention Coverage Sliders</CardTitle>
              {activePreset && (
                <span className="text-xs text-emerald-600 font-medium dark:text-emerald-400">
                  Customizing: {SIMULATION_PRESETS.find((p) => p.id === activePreset)?.name}
                </span>
              )}
            </div>
            <CardDescription>Coverage is the % of the ward&apos;s eligible surface converted to each intervention.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {catalog.data.map((item) => (
              <div key={item.type} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <label className="font-medium">{item.label}</label>
                  <span className="tabular-nums text-slate-500 font-semibold">{coverage[item.type] ?? 0}%</span>
                </div>
                <Slider
                  min={0}
                  max={item.max_coverage_pct}
                  step={1}
                  value={coverage[item.type] ?? 0}
                  onChange={(e) => {
                    setActivePreset(null);
                    setCoverage((c) => ({ ...c, [item.type]: Number(e.target.value) }));
                  }}
                />
                <p className="text-xs text-slate-400">{item.description}</p>
              </div>
            ))}
            {error && <Alert variant="destructive">{error}</Alert>}
            <Button className="w-full gap-2" onClick={runSimulation} disabled={running}>
              <FlaskConical className="h-4 w-4" />
              {running ? "Simulating with Physics Engine..." : "Run Physics Simulation"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Simulation result</CardTitle>
            <CardDescription>Physics-derived surface temperature reduction and environmental impacts.</CardDescription>
          </CardHeader>
          <CardContent>
            {!result ? (
              <p className="py-10 text-center text-sm text-slate-400">Run a simulation to see cooling impact, cost, and resource needs.</p>
            ) : (
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={beforeAfterData}>
                    <CartesianGrid vertical={false} stroke={CHART.grid} />
                    <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke={CHART.axis} />
                    <YAxis unit="°C" tick={{ fontSize: 12 }} stroke={CHART.axis} domain={["auto", "auto"]} />
                    <Tooltip formatter={(v) => `${Number(v).toFixed(1)}°C`} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {beforeAfterData.map((d, i) => (
                        <Cell key={i} fill={heatColor(i === 0 ? 90 : 40)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Metric label="Expected cooling" value={`${result.expected_cooling_c}°C`} sub={`CI ${result.cooling_ci_low}–${result.cooling_ci_high}°C`} />
                  <Metric label="Confidence" value={`${(result.confidence * 100).toFixed(0)}%`} />
                  <Metric label="Cost" value={formatCurrency(result.cost_usd)} />
                  <Metric label="Land required" value={`${result.land_km2.toFixed(3)} km²`} />
                  <Metric label="Water / year" value={`${formatNumber(result.water_m3_per_year)} m³`} />
                  <Metric label="Population benefited" value={formatNumber(result.population_benefited)} />
                </div>

                <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
                  <span>Risk: <RiskBadge risk={result.baseline_risk} /> → <RiskBadge risk={result.simulated_risk} /></span>
                  <span className="font-medium text-emerald-600">-{result.risk_reduction_pct}% Risk Reduction</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Baseline vs Intervention Comparative Delta Analysis */}
      {result && (
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-emerald-600" />
              Baseline vs. Intervention Comparative Analysis
            </CardTitle>
            <CardDescription className="text-xs">
              Direct quantification of cooling effectiveness, resource intensity, and population protection efficiency.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-900/40">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <TrendingDown className="h-3.5 w-3.5 text-emerald-500" />
                  Net Delta LST (ΔT)
                </div>
                <div className="mt-1.5 text-xl font-bold text-emerald-600 dark:text-emerald-400">
                  -{result.expected_cooling_c.toFixed(2)}°C
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {result.baseline_lst.toFixed(1)}°C → {result.simulated_lst.toFixed(1)}°C
                </div>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-900/40">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <DollarSign className="h-3.5 w-3.5 text-blue-500" />
                  Cost Efficiency
                </div>
                <div className="mt-1.5 text-xl font-bold text-slate-800 dark:text-slate-100">
                  {costPerTenthDegree > 0 ? formatCurrency(costPerTenthDegree) : "N/A"}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Per 0.1°C temperature reduction
                </div>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-900/40">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <Droplets className="h-3.5 w-3.5 text-cyan-500" />
                  Water Intensity
                </div>
                <div className="mt-1.5 text-xl font-bold text-slate-800 dark:text-slate-100">
                  {waterPerDegree > 0 ? `${formatNumber(Math.round(waterPerDegree))} m³` : "0 m³"}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Annual water required per 1.0°C cooled
                </div>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-900/40">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <Users className="h-3.5 w-3.5 text-indigo-500" />
                  Protected Population
                </div>
                <div className="mt-1.5 text-xl font-bold text-slate-800 dark:text-slate-100">
                  {formatNumber(result.population_benefited)}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {((result.population_benefited / (ward.data.population_total || 1)) * 100).toFixed(0)}% of ward population
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-semibold tabular-nums">{value}</p>
      {sub && <p className="text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

export default function SimulationPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <SimulationContent />
    </Suspense>
  );
}
