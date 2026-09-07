"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { WardPicker } from "@/components/ward-picker";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState, EmptyState } from "@/components/ui/empty-state";
import { formatCurrency, formatNumber } from "@/lib/utils";
import { ListChecks } from "lucide-react";

function RecommendationsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const wardId = searchParams.get("ward");

  if (!wardId) {
    return <WardPicker title="Recommendations" description="Select a ward to see its actionable recommendations." onSelect={(id) => router.push(`/recommendations?ward=${id}`)} />;
  }
  return <RecommendationsForWard wardId={wardId} onChangeWard={() => router.push("/recommendations")} />;
}

function RecommendationsForWard({ wardId, onChangeWard }: { wardId: string; onChangeWard: () => void }) {
  const router = useRouter();
  const recs = useApi(() => api.recommendations.forWard(wardId), [wardId]);

  if (recs.loading) return <FullPageSpinner />;
  if (recs.error) return <ErrorState message={recs.error} onRetry={recs.reload} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Recommendations {recs.data?.[0] ? `— ${recs.data[0].ward_name}` : ""}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Generated from your most recent optimization run for this ward.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onChangeWard}>
            Change ward
          </Button>
          <Button size="sm" onClick={() => (router.push(`/optimization?ward=${wardId}`))}>
            Run new optimization
          </Button>
        </div>
      </div>

      {recs.data && recs.data.length === 0 && (
        <EmptyState
          icon={ListChecks}
          title="No recommendations yet"
          description="Run the optimizer for this ward first — recommendations are generated from its results."
          action={
            <Button size="sm" onClick={() => (router.push(`/optimization?ward=${wardId}`))}>
              Go to optimizer
            </Button>
          }
        />
      )}

      <div className="space-y-3">
        {recs.data?.map((r) => (
          <Card key={r.id}>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-center gap-2">
                <Badge>Rank {r.rank}</Badge>
                <p className="font-semibold">{r.title}</p>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300">{r.narrative_text}</p>
              <div className="grid grid-cols-2 gap-2 pt-1 text-xs sm:grid-cols-4">
                <Stat label="Cooling" value={`${r.metrics.expected_cooling_c}°C`} />
                <Stat label="Cost" value={formatCurrency(r.metrics.cost_usd)} />
                <Stat label="Population" value={formatNumber(r.metrics.population_benefited)} />
                <Stat label="Confidence" value={`${(r.metrics.confidence * 100).toFixed(0)}%`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 px-2 py-1.5 dark:bg-slate-800">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="font-semibold tabular-nums">{value}</p>
    </div>
  );
}

export default function RecommendationsPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <RecommendationsContent />
    </Suspense>
  );
}
