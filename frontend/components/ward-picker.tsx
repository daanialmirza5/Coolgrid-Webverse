"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { useCity } from "@/lib/city-context";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { RiskBadge } from "@/components/ui/risk-badge";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { MapPin } from "lucide-react";

export function WardPicker({ title, description, onSelect }: { title: string; description: string; onSelect: (wardId: string) => void }) {
  const { city } = useCity();
  const [query, setQuery] = useState("");
  const hotspots = useApi(() => (city ? api.hotspots.list(city.id) : Promise.reject(new Error("no city"))), [city?.id]);

  if (hotspots.loading) return <FullPageSpinner label="Loading wards..." />;
  if (hotspots.error) return <ErrorState message={hotspots.error} onRetry={hotspots.reload} />;

  const filtered = (hotspots.data ?? []).filter((h) => h.ward_name.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">{title}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
      </div>
      <Input placeholder="Search wards..." value={query} onChange={(e) => setQuery(e.target.value)} className="max-w-xs" />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((h) => (
          <Card key={h.ward_id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(h.ward_id)}>
            <CardContent className="flex items-center justify-between p-3">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-sm font-medium">{h.ward_name}</p>
                  <p className="text-xs text-slate-400">{h.lst_celsius}°C</p>
                </div>
              </div>
              <RiskBadge risk={h.risk_level} />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
