"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CartesianGrid, ErrorBar, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { WardPicker } from "@/components/ward-picker";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { Alert } from "@/components/ui/alert";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Button } from "@/components/ui/button";
import { CHART } from "@/lib/colors";

function PredictionsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Predictions" description="Select a ward to see its short/medium-term heat forecast." onSelect={(id) => router.push(`/predictions?ward=${id}`)} />;
  }
  return <PredictionsForWard wardId={wardId} onChangeWard={() => router.push("/predictions")} />;
}

function PredictionsForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const prediction = useApi(() => api.predictions.forWard(wardId), [wardId]);

  if (prediction.loading) return <FullPageSpinner label="Forecasting..." />;
  if (prediction.error) return <ErrorState message={prediction.error} onRetry={prediction.reload} />;
  if (!prediction.data) return null;
  const p = prediction.data;

  const chartData = [
    { label: "Today", horizon: 0, predicted_lst: p.current_lst, errorY: [0, 0] },
    ...p.points.map((pt) => ({
      label: `+${pt.horizon_days}d`,
      horizon: pt.horizon_days,
      predicted_lst: pt.predicted_lst,
      errorY: [pt.predicted_lst - pt.predicted_lst_lower, pt.predicted_lst_upper - pt.predicted_lst],
    })),
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">{p.ward_name} — Heat Forecast</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">As of {p.as_of} · current LST {p.current_lst}°C</p>
        </div>
        <Button variant="outline" size="sm" onClick={onChangeWard}>
          Change ward
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicted land surface temperature</CardTitle>
          <CardDescription>Error bars show the model&apos;s confidence range, which widens at longer horizons.</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ left: 0, right: 16, top: 10 }}>
              <CartesianGrid stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke={CHART.axis} />
              <YAxis unit="°C" tick={{ fontSize: 12 }} stroke={CHART.axis} domain={["auto", "auto"]} />
              <Tooltip formatter={(v) => `${Number(v).toFixed(1)}°C`} />
              <Line type="monotone" dataKey="predicted_lst" stroke={CHART.primary} strokeWidth={2} dot={{ r: 4 }}>
                <ErrorBar dataKey="errorY" width={6} strokeWidth={2} stroke={CHART.primary} opacity={0.4} direction="y" />
              </Line>
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {p.points.map((pt) => (
          <Card key={pt.horizon_days}>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold">+{pt.horizon_days} day{pt.horizon_days > 1 ? "s" : ""}</p>
                <RiskBadge risk={pt.risk_level} />
              </div>
              <p className="text-2xl font-bold tabular-nums">{pt.predicted_lst}°C</p>
              <p className="text-xs text-slate-500">
                Range {pt.predicted_lst_lower}–{pt.predicted_lst_upper}°C · {pt.change_from_current_c > 0 ? "+" : ""}
                {pt.change_from_current_c}°C vs today
              </p>
              <p className="text-xs text-slate-400">Confidence {(pt.confidence * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Alert variant="warning">{p.points[0]?.disclaimer}</Alert>
    </div>
  );
}

export default function PredictionsPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <PredictionsContent />
    </Suspense>
  );
}
