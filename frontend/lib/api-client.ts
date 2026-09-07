import type {
  AuditLogEntry,
  City,
  DashboardSummary,
  DataSourceStatus,
  DriverAnalysis,
  Hotspot,
  InterventionCatalogItem,
  InterventionInput,
  OptimizationConstraintsInput,
  OptimizationRun,
  PredictionResponse,
  Recommendation,
  ReportOut,
  SimulationResult,
  SystemStatus,
  TokenResponse,
  User,
  UserRole,
  Ward,
  WardComparisonRow,
  WardGeoJSON,
} from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ACCESS_KEY = "coolgrid_access_token";
const REFRESH_KEY = "coolgrid_refresh_token";

export function getStoredTokens() {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: window.localStorage.getItem(ACCESS_KEY),
    refresh: window.localStorage.getItem(REFRESH_KEY),
  };
}

export function storeTokens(access: string, refresh: string) {
  window.localStorage.setItem(ACCESS_KEY, access);
  window.localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const { refresh } = getStoredTokens();
  if (!refresh) return false;
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    })
      .then(async (res) => {
        if (!res.ok) return false;
        const data: TokenResponse = await res.json();
        storeTokens(data.access_token, data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

// These endpoints take credentials/tokens as *input* -- a 401 from them means
// "wrong password" / "invalid token", not "your session expired", so they
// must never go through the refresh-and-retry flow below (which would
// swallow the real error and replace it with a generic "session expired"
// message -- a real bug caught by this project's own E2E tests).
const AUTH_ENDPOINTS_EXEMPT_FROM_REFRESH = new Set([
  "/api/auth/login",
  "/api/auth/register",
  "/api/auth/refresh",
  "/api/auth/forgot-password",
  "/api/auth/reset-password",
]);

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const { access } = getStoredTokens();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    ...(access ? { Authorization: `Bearer ${access}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry && !AUTH_ENDPOINTS_EXEMPT_FROM_REFRESH.has(path)) {
    const refreshed = await tryRefresh();
    if (refreshed) return request<T>(path, options, false);
    clearTokens();
    // A hard navigation is deliberate here: this module sits outside React
    // (no access to useRouter), and a full reload guarantees every
    // component's in-memory state is cleared along with the expired session.
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/login";
    }
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (res.status === 204) return undefined as T;

  let body: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }

  return body as T;
}

const get = <T>(path: string) => request<T>(path, { method: "GET" });
const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: "POST", body: data !== undefined ? JSON.stringify(data) : undefined });
const patch = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: "PATCH", body: data !== undefined ? JSON.stringify(data) : undefined });

export const api = {
  auth: {
    login: (email: string, password: string) => post<TokenResponse>("/api/auth/login", { email, password }),
    register: (email: string, password: string, full_name: string, organization?: string) =>
      post<TokenResponse>("/api/auth/register", { email, password, full_name, organization }),
    me: () => get<User>("/api/auth/me"),
    logout: () => post<void>("/api/auth/logout"),
    forgotPassword: (email: string) =>
      post<{ message: string; demo_note?: string; reset_token?: string }>("/api/auth/forgot-password", { email }),
    resetPassword: (token: string, new_password: string) =>
      post<void>("/api/auth/reset-password", { token, new_password }),
  },
  cities: {
    list: () => get<City[]>("/api/cities"),
    get: (id: string) => get<City>(`/api/cities/${id}`),
    wards: (id: string) => get<Ward[]>(`/api/cities/${id}/wards`),
    wardsGeoJSON: (id: string) => get<WardGeoJSON>(`/api/cities/${id}/wards.geojson`),
  },
  wards: {
    get: (id: string) => get<Ward>(`/api/wards/${id}`),
  },
  dashboard: {
    summary: (cityId?: string) => get<DashboardSummary>(`/api/dashboard/summary${cityId ? `?city_id=${cityId}` : ""}`),
  },
  hotspots: {
    list: (cityId?: string, risk?: string) => {
      const params = new URLSearchParams();
      if (cityId) params.set("city_id", cityId);
      if (risk) params.set("risk", risk);
      const qs = params.toString();
      return get<Hotspot[]>(`/api/hotspots${qs ? `?${qs}` : ""}`);
    },
    forWard: (wardId: string) => get<Hotspot>(`/api/wards/${wardId}/hotspot`),
  },
  drivers: {
    forWard: (wardId: string) => get<DriverAnalysis>(`/api/wards/${wardId}/drivers`),
  },
  predictions: {
    forWard: (wardId: string) => get<PredictionResponse>(`/api/wards/${wardId}/predictions`),
  },
  comparison: {
    wards: (cityId?: string) => get<WardComparisonRow[]>(`/api/comparison/wards${cityId ? `?city_id=${cityId}` : ""}`),
  },
  interventions: {
    catalog: () => get<InterventionCatalogItem[]>("/api/interventions/catalog"),
  },
  simulations: {
    run: (wardId: string, interventions: InterventionInput[]) =>
      post<SimulationResult>("/api/simulations", { ward_id: wardId, interventions }),
    get: (id: string) => get<SimulationResult>(`/api/simulations/${id}`),
  },
  optimizations: {
    run: (constraints: OptimizationConstraintsInput) => post<OptimizationRun>("/api/optimizations", constraints),
  },
  recommendations: {
    forWard: (wardId: string) => get<Recommendation[]>(`/api/wards/${wardId}/recommendations`),
  },
  reports: {
    create: (payload: { ward_id?: string; city_id?: string; simulation_id?: string; optimization_run_id?: string; title?: string }) =>
      post<ReportOut>("/api/reports", payload),
    list: () => get<ReportOut[]>("/api/reports"),
    get: (id: string) => get<ReportOut>(`/api/reports/${id}`),
    // The download endpoint requires a Bearer token, which a plain <a href>
    // navigation never attaches (no cookies are used for auth) -- fetch it
    // as an authenticated blob instead and hand the caller an object URL.
    downloadBlobUrl: async (id: string): Promise<string> => {
      const { access } = getStoredTokens();
      const res = await fetch(`${API_BASE}/api/reports/${id}/download`, {
        headers: access ? { Authorization: `Bearer ${access}` } : {},
      });
      if (!res.ok) throw new ApiError(res.status, "Could not download report");
      const blob = await res.blob();
      return URL.createObjectURL(blob);
    },
  },
  datasources: {
    status: () => get<DataSourceStatus>("/api/datasources/status"),
  },
  users: {
    updateProfile: (data: { full_name?: string; organization?: string }) => patch<User>("/api/users/me", data),
    changePassword: (current_password: string, new_password: string) =>
      post<void>("/api/users/me/change-password", { current_password, new_password }),
  },
  admin: {
    systemStatus: () => get<SystemStatus>("/api/admin/system-status"),
    listUsers: () => get<User[]>("/api/admin/users"),
    updateUser: (id: string, role: UserRole, is_active?: boolean) =>
      patch<User>(`/api/admin/users/${id}`, { role, is_active }),
    auditLogs: (limit = 100) => get<AuditLogEntry[]>(`/api/admin/audit-logs?limit=${limit}`),
  },
};
