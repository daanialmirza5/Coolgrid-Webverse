"use client";

import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { CheckCircle2, CloudOff, Database, Users2, Wind } from "lucide-react";

const ICONS = { satellite: CloudOff, weather: Wind, urban: Database, population: Users2 } as const;

export default function DataSourcesPage() {
  const status = useApi(() => api.datasources.status(), []);

  if (status.loading) return <FullPageSpinner label="Checking data sources..." />;
  if (status.error) return <ErrorState message={status.error} onRetry={status.reload} />;
  if (!status.data) return null;
  const s = status.data;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Data Sources &amp; Model Status</h1>

      {s.all_demo && (
        <Alert variant="warning">
          All data sources are running in <strong>DEMO mode</strong>. No real Landsat, Sentinel-2, ERA5, or census
          credentials are configured — CoolGrid is using synthetic demonstration data throughout. The provider
          architecture supports plugging in real sources without any application changes.
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {(["satellite", "weather", "urban", "population"] as const).map((key) => {
          const Icon = ICONS[key];
          const provider = s[key];
          return (
            <Card key={key}>
              <CardContent className="space-y-2 p-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  <Icon className="h-4 w-4" />
                </div>
                <p className="text-sm font-semibold capitalize">{key}</p>
                <p className="text-xs text-slate-500">{provider.provider}</p>
                <Badge variant={provider.is_demo ? "secondary" : "default"}>{provider.is_demo ? "DEMO" : "LIVE"}</Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {s.notes.map((n, i) => (
            <p key={i} className="text-sm text-slate-600 dark:text-slate-300">
              {n}
            </p>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model status</CardTitle>
          <CardDescription>Heat detection model version {s.detection_model_version}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Object.entries(s.detection_model_metrics).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                <p className="text-xs uppercase text-slate-400">{k}</p>
                <p className="font-semibold tabular-nums">{typeof v === "number" ? v.toFixed(3) : String(v)}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 text-sm">
            {s.pinn_trained ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <CloudOff className="h-4 w-4 text-slate-400" />}
            Physics-informed neural network (PINN): {s.pinn_trained ? "trained and available" : "not trained"}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
