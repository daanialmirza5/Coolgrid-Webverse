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
import { FlaskConical } from "lucide-react";

function SimulationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Simulation" description="Select a ward to test cooling interventions." onSelect={(id) => router.push(`/simulation?ward=${id}`)} />;
  }
  return <SimulationForWard wardId={wardId} onChangeWard={() => router.push("/simulation")} />;
}

function SimulationForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const catalog = useApi(() => api.interventions.catalog(), []);
  const ward = useApi(() => api.wards.get(wardId), [wardId]);
  const [coverage, setCoverage] = useState<Record<string, number>>({});
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (catalog.loading || ward.loading) return <FullPageSpinner label="Loading intervention catalog..." />;
  if (catalog.error) return <ErrorState message={catalog.error} onRetry={catalog.reload} />;
  if (!catalog.data || !ward.data) return null;

  async function runSimulation() {
    const interventions = Object.entries(coverage)
      .filter(([, v]) => v > 0)
      .map(([type, coverage_pct]) => ({ type: type as InterventionType, coverage_pct }));
    if (interventions.length === 0) {
      setError("Set at least one intervention above 0% coverage.");
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
        { label: "Baseline", value: result.baseline_lst },
        { label: "Simulated", value: result.simulated_lst },
      ]
    : [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Simulate Interventions — {ward.data.name}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Adjust coverage for each intervention type and run the physics-based simulation.</p>
        </div>
        <Button variant="outline" size="sm" onClick={onChangeWard}>
          Change ward
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Intervention coverage</CardTitle>
            <CardDescription>Coverage is the % of the ward&apos;s eligible surface converted to each intervention.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {catalog.data.map((item) => (
              <div key={item.type} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <label className="font-medium">{item.label}</label>
                  <span className="tabular-nums text-slate-500">{coverage[item.type] ?? 0}%</span>
                </div>
                <Slider
                  min={0}
                  max={item.max_coverage_pct}
                  step={1}
                  value={coverage[item.type] ?? 0}
                  onChange={(e) => setCoverage((c) => ({ ...c, [item.type]: Number(e.target.value) }))}
                />
                <p className="text-xs text-slate-400">{item.description}</p>
              </div>
            ))}
            {error && <Alert variant="destructive">{error}</Alert>}
            <Button className="w-full gap-2" onClick={runSimulation} disabled={running}>
              <FlaskConical className="h-4 w-4" />
              {running ? "Simulating..." : "Run simulation"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Simulation result</CardTitle>
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
                  <span className="font-medium text-emerald-600">-{result.risk_reduction_pct}%</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
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
