"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { WardPicker } from "@/components/ward-picker";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { CHART } from "@/lib/colors";
import { Button } from "@/components/ui/button";

function DriverAnalysisContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Driver Analysis" description="Select a ward to see why it is hot." onSelect={(id) => router.push(`/drivers?ward=${id}`)} />;
  }
  return <DriverAnalysisForWard wardId={wardId} onChangeWard={() => router.push("/drivers")} />;
}

function DriverAnalysisForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const analysis = useApi(() => api.drivers.forWard(wardId), [wardId]);

  if (analysis.loading) return <FullPageSpinner label="Explaining this hotspot..." />;
  if (analysis.error) return <ErrorState message={analysis.error} onRetry={analysis.reload} />;
  if (!analysis.data) return null;
  const d = analysis.data;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Why is {d.ward_name} hot?</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">SHAP-based driver attribution · current LST {d.lst_celsius}°C</p>
        </div>
        <Button variant="outline" size="sm" onClick={onChangeWard}>
          Change ward
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <p className="text-sm">{d.narrative}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Driver contributions</CardTitle>
          <CardDescription>
            Red bars push temperature up, green bars help cool this ward. Bar length is each driver&apos;s share of the total explanation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={Math.max(280, d.drivers.length * 36)}>
            <BarChart data={d.drivers} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid horizontal={false} stroke={CHART.grid} />
              <XAxis type="number" unit="%" tick={{ fontSize: 11 }} stroke={CHART.axis} />
              <YAxis dataKey="label" type="category" width={220} tick={{ fontSize: 11 }} stroke={CHART.axis} />
              <Tooltip
                formatter={(value, _name, entry) => [`${Number(value)}%`, entry.payload.direction === "increases_heat" ? "Warms" : "Cools"]}
              />
              <Bar dataKey="relative_contribution_pct" radius={[0, 4, 4, 0]}>
                {d.drivers.map((driver, i) => (
                  <Cell key={i} fill={driver.direction === "increases_heat" ? CHART.warms : CHART.cools} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 flex gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CHART.warms }} /> Increases heat
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CHART.cools }} /> Decreases heat
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function DriversPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <DriverAnalysisContent />
    </Suspense>
  );
}
