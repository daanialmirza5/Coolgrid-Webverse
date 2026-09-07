"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import { AdminGuard } from "@/components/layout/auth-guard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Alert } from "@/components/ui/alert";
import { FullPageSpinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/ui/empty-state";
import type { UserRole } from "@/lib/types";
import { CheckCircle2, XCircle } from "lucide-react";
import { formatDate } from "@/lib/utils";

function AdminContent() {
  const status = useApi(() => api.admin.systemStatus(), []);
  const users = useApi(() => api.admin.listUsers(), []);
  const auditLogs = useApi(() => api.admin.auditLogs(30), []);
  const [error, setError] = useState<string | null>(null);

  async function updateRole(userId: string, role: UserRole) {
    setError(null);
    try {
      await api.admin.updateUser(userId, role);
      users.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update user");
    }
  }

  if (status.loading) return <FullPageSpinner label="Loading system status..." />;
  if (status.error) return <ErrorState message={status.error} onRetry={status.reload} />;
  if (!status.data) return null;
  const s = status.data;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Admin — System Status</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatusTile label="Database" ok={s.database_connected} />
        <MiniStat label="Cities" value={s.city_count} />
        <MiniStat label="Wards" value={s.ward_count} />
        <MiniStat label="Users" value={s.user_count} />
        <MiniStat label="Simulations" value={s.simulation_count} />
        <MiniStat label="Optimization runs" value={s.optimization_run_count} />
        <MiniStat label="Heat maps generated" value={s.heat_map_count} />
        <StatusTile label="Demo data mode" ok={s.data_sources.all_demo} okLabel="All demo" badLabel="Live sources" invert />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model runs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {s.model_runs.map((m, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-800">
              <span className="font-medium">{m.model_name}</span>
              <span className="text-slate-400">{m.version}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {error && <Alert variant="destructive">{error}</Alert>}
          {users.data?.map((u) => (
            <div key={u.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800">
              <div>
                <p className="text-sm font-medium">{u.full_name}</p>
                <p className="text-xs text-slate-400">{u.email}</p>
              </div>
              <div className="flex items-center gap-2">
                {!u.is_active && <Badge variant="outline">inactive</Badge>}
                <Select value={u.role} onChange={(e) => updateRole(u.id, e.target.value as UserRole)} className="w-32">
                  <option value="viewer">viewer</option>
                  <option value="analyst">analyst</option>
                  <option value="admin">admin</option>
                </Select>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent audit log</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400 dark:border-slate-800">
                <th className="px-4 py-2">Time</th>
                <th className="px-4 py-2">Action</th>
                <th className="px-4 py-2">Resource</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.data?.map((a) => (
                <tr key={a.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="px-4 py-2 text-xs text-slate-400">{formatDate(a.created_at)}</td>
                  <td className="px-4 py-2 font-medium">{a.action}</td>
                  <td className="px-4 py-2 text-slate-500">{a.resource_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusTile({ label, ok, okLabel = "Connected", badLabel = "Down", invert = false }: { label: string; ok: boolean; okLabel?: string; badLabel?: string; invert?: boolean }) {
  const good = invert ? ok : ok;
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        {good ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-red-600" />}
        <div>
          <p className="text-xs text-slate-500">{label}</p>
          <p className="text-sm font-semibold">{good ? okLabel : badLabel}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-2xl font-bold tabular-nums">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function AdminPage() {
  return (
    <AdminGuard>
      <AdminContent />
    </AdminGuard>
  );
}
