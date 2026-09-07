"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { useCity } from "@/lib/city-context";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Alert } from "@/components/ui/alert";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState, EmptyState } from "@/components/ui/empty-state";
import { formatDate } from "@/lib/utils";
import { Download, FileText } from "lucide-react";

export default function ReportsPage() {
  const { city } = useCity();
  const wards = useApi(() => (city ? api.cities.wards(city.id) : Promise.reject(new Error("no city"))), [city?.id]);
  const reports = useApi(() => api.reports.list(), []);
  const [scope, setScope] = useState<"city" | "ward">("city");
  const [wardId, setWardId] = useState<string>("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  async function downloadReport(id: string, title: string) {
    setError(null);
    setDownloadingId(id);
    try {
      const blobUrl = await api.reports.downloadBlobUrl(id);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${title}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10_000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not download report");
    } finally {
      setDownloadingId(null);
    }
  }

  async function generateReport() {
    if (!city) return;
    setError(null);
    setGenerating(true);
    try {
      await api.reports.create(scope === "city" ? { city_id: city.id } : { ward_id: wardId || wards.data?.[0]?.id });
      reports.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Report generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Reports</h1>

      <Card>
        <CardHeader>
          <CardTitle>Generate a new report</CardTitle>
          <CardDescription>Includes heat situation, drivers, predictions, and your latest simulation/optimization for the selected scope.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div className="space-y-1.5">
            <Label>Scope</Label>
            <Select value={scope} onChange={(e) => setScope(e.target.value as "city" | "ward")} className="w-40">
              <option value="city">City-wide</option>
              <option value="ward">Single ward</option>
            </Select>
          </div>
          {scope === "ward" && (
            <div className="space-y-1.5">
              <Label>Ward</Label>
              <Select value={wardId} onChange={(e) => setWardId(e.target.value)} className="w-56">
                <option value="">Select a ward...</option>
                {wards.data?.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </Select>
            </div>
          )}
          <Button onClick={generateReport} disabled={generating} className="gap-2">
            <FileText className="h-4 w-4" />
            {generating ? "Generating..." : "Generate report"}
          </Button>
        </CardContent>
        {error && (
          <CardContent className="pt-0">
            <Alert variant="destructive">{error}</Alert>
          </CardContent>
        )}
      </Card>

      {reports.loading && <FullPageSpinner />}
      {reports.error && <ErrorState message={reports.error} onRetry={reports.reload} />}
      {reports.data && reports.data.length === 0 && <EmptyState icon={FileText} title="No reports yet" description="Generate your first report above." />}

      <div className="space-y-2">
        {reports.data?.map((r) => (
          <Card key={r.id}>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{r.title}</p>
                <p className="text-xs text-slate-400">
                  {formatDate(r.created_at)} ·{" "}
                  <span
                    className={
                      r.status === "ready" ? "text-emerald-600" : r.status === "failed" ? "text-red-600" : "text-amber-600"
                    }
                  >
                    {r.status}
                  </span>
                </p>
              </div>
              {r.status === "ready" && r.download_url && (
                <Button size="sm" variant="outline" className="gap-1.5" disabled={downloadingId === r.id} onClick={() => downloadReport(r.id, r.title)}>
                  <Download className="h-3.5 w-3.5" /> {downloadingId === r.id ? "Downloading..." : "Download PDF"}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
