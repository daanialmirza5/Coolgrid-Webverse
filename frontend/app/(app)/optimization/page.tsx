"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { WardPicker } from "@/components/ward-picker";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState, EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { OptimizationRun } from "@/lib/types";
import { Target } from "lucide-react";

function OptimizationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Optimization" description="Select a ward to find the best cooling strategy under your constraints." onSelect={(id) => router.push(`/optimization?ward=${id}`)} />;
  }
  return <OptimizationForWard wardId={wardId} onChangeWard={() => router.push("/optimization")} />;
}

function OptimizationForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const router = useRouter();
  const ward = useApi(() => api.wards.get(wardId), [wardId]);
  const [budget, setBudget] = useState(50_000_000);
  const [land, setLand] = useState(3);
  const [water, setWater] = useState(2_000_000);
  const [populationPriority, setPopulationPriority] = useState(1);
  const [riskPriority, setRiskPriority] = useState(1);
  const [run, setRun] = useState<OptimizationRun | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (ward.loading) return <FullPageSpinner />;
  if (ward.error) return <ErrorState message={ward.error} onRetry={ward.reload} />;

  async function runOptimization() {
    setError(null);
    setRunning(true);
    try {
      const res = await api.optimizations.run({
        ward_id: wardId,
        budget_usd: budget,
        land_km2: land,
        water_m3_per_year: water,
        population_priority: populationPriority,
        risk_priority: riskPriority,
      });
      setRun(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Optimization failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Optimize — {ward.data?.name}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Set constraints and let CoolGrid rank intervention portfolios.</p>
        </div>
        <Button variant="outline" size="sm" onClick={onChangeWard}>
          Change ward
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Constraints</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Budget: {formatCurrency(budget)}</Label>
              <Slider min={1_000_000} max={200_000_000} step={1_000_000} value={budget} onChange={(e) => setBudget(Number(e.target.value))} />
              <Input type="number" value={budget} onChange={(e) => setBudget(Number(e.target.value))} className="mt-1" />
            </div>
            <div className="space-y-1.5">
              <Label>Available land: {land.toFixed(1)} km²</Label>
              <Slider min={0.1} max={10} step={0.1} value={land} onChange={(e) => setLand(Number(e.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label>Available water: {formatNumber(water)} m³/yr</Label>
              <Slider min={100_000} max={10_000_000} step={100_000} value={water} onChange={(e) => setWater(Number(e.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label>Population priority: {populationPriority.toFixed(1)}×</Label>
              <Slider min={0} max={2} step={0.1} value={populationPriority} onChange={(e) => setPopulationPriority(Number(e.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label>Risk-reduction priority: {riskPriority.toFixed(1)}×</Label>
              <Slider min={0} max={2} step={0.1} value={riskPriority} onChange={(e) => setRiskPriority(Number(e.target.value))} />
            </div>
            {error && <Alert variant="destructive">{error}</Alert>}
            <Button className="w-full gap-2" onClick={runOptimization} disabled={running}>
              <Target className="h-4 w-4" />
              {running ? "Optimizing..." : "Run optimization"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-3 lg:col-span-2">
          {!run && !running && (
            <EmptyState icon={Target} title="No optimization run yet" description="Set your constraints and run the optimizer to see ranked strategies." />
          )}
          {run && run.strategies.length === 0 && (
            <EmptyState icon={Target} title="No feasible strategy found" description="Try increasing your budget, land, or water constraints." />
          )}
          {run?.strategies.map((s) => (
            <Card key={s.rank}>
              <CardContent className="space-y-2 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge>#{s.rank}</Badge>
                    <p className="font-semibold">{s.interventions.map((i) => i.label).join(" + ")}</p>
                  </div>
                  <p className="text-xs text-slate-400">Score {s.score}</p>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-300">{s.reason}</p>
                <div className="grid grid-cols-2 gap-2 pt-1 text-xs sm:grid-cols-4">
                  <MiniStat label="Cooling" value={`${s.expected_cooling_c}°C`} />
                  <MiniStat label="Cost" value={formatCurrency(s.cost_usd)} />
                  <MiniStat label="Population" value={formatNumber(s.population_benefited)} />
                  <MiniStat label="Confidence" value={`${(s.confidence * 100).toFixed(0)}%`} />
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {s.interventions.map((i) => (
                    <Badge key={i.type} variant="secondary">
                      {i.label}: {i.coverage_pct}%
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {run && run.strategies.length > 0 && (
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => router.push(`/recommendations?ward=${wardId}`)}>
            View recommendations →
          </Button>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 px-2 py-1.5 dark:bg-slate-800">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="font-semibold tabular-nums">{value}</p>
    </div>
  );
}

export default function OptimizationPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <OptimizationContent />
    </Suspense>
  );
}
