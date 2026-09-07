"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { useCity } from "@/lib/city-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import { RISK_COLOR } from "@/lib/colors";
import { formatNumber } from "@/lib/utils";

type SortKey = "lst_celsius" | "heat_score" | "population_total" | "green_space_pct";

export default function ComparisonPage() {
  const { city } = useCity();
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("lst_celsius");
  const comparison = useApi(() => (city ? api.comparison.wards(city.id) : Promise.reject(new Error("no city"))), [city?.id]);

  const sorted = useMemo(() => {
    if (!comparison.data) return [];
    return [...comparison.data].sort((a, b) => b[sortKey] - a[sortKey]);
  }, [comparison.data, sortKey]);

  if (comparison.loading) return <FullPageSpinner label="Loading ward comparison..." />;
  if (comparison.error) return <ErrorState message={comparison.error} onRetry={comparison.reload} />;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Ward Comparison</h1>

      <Card>
        <CardHeader>
          <CardTitle>Land surface temperature by ward</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={Math.max(300, sorted.length * 22)}>
            <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid horizontal={false} stroke="#e1e0d9" />
              <XAxis type="number" unit="°C" tick={{ fontSize: 11 }} />
              <YAxis dataKey="ward_name" type="category" width={80} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v) => `${Number(v)}°C`} />
              <Bar dataKey="lst_celsius" radius={[0, 4, 4, 0]}>
                {sorted.map((row, i) => (
                  <Cell key={i} fill={RISK_COLOR[row.risk_level]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ward details</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400 dark:border-slate-800">
                <th className="px-4 py-2">Ward</th>
                <th className="px-4 py-2">Archetype</th>
                <SortableHeader label="LST" sortKey="lst_celsius" active={sortKey} onSort={setSortKey} />
                <SortableHeader label="Heat Score" sortKey="heat_score" active={sortKey} onSort={setSortKey} />
                <th className="px-4 py-2">Risk</th>
                <SortableHeader label="Vegetation" sortKey="green_space_pct" active={sortKey} onSort={setSortKey} />
                <th className="px-4 py-2">Built-up</th>
                <SortableHeader label="Population" sortKey="population_total" active={sortKey} onSort={setSortKey} />
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr
                  key={row.ward_id}
                  className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
                  onClick={() => router.push(`/hotspots/${row.ward_id}`)}
                >
                  <td className="px-4 py-2 font-medium">{row.ward_name}</td>
                  <td className="px-4 py-2 capitalize text-slate-500">{row.archetype.replace(/_/g, " ")}</td>
                  <td className="px-4 py-2 tabular-nums">{row.lst_celsius}°C</td>
                  <td className="px-4 py-2 tabular-nums">{row.heat_score}</td>
                  <td className="px-4 py-2">
                    <RiskBadge risk={row.risk_level} />
                  </td>
                  <td className="px-4 py-2 tabular-nums">{row.green_space_pct}%</td>
                  <td className="px-4 py-2 tabular-nums">{(row.built_up_density * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2 tabular-nums">{formatNumber(row.population_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function SortableHeader({
  label,
  sortKey,
  active,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  active: SortKey;
  onSort: (k: SortKey) => void;
}) {
  return (
    <th className="cursor-pointer px-4 py-2 hover:text-slate-700 dark:hover:text-slate-200" onClick={() => onSort(sortKey)}>
      {label} {active === sortKey && "↓"}
    </th>
  );
}
