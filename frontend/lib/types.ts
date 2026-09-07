export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type UserRole = "admin" | "analyst" | "viewer";
export type InterventionType =
  | "urban_trees"
  | "cool_roofs"
  | "green_roofs"
  | "vegetation_corridors"
  | "blue_infrastructure"
  | "reflective_surfaces";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization: string | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface City {
  id: string;
  slug: string;
  name: string;
  country: string;
  is_demo: boolean;
  bbox: [number, number, number, number];
}

export interface Ward {
  id: string;
  city_id: string;
  ward_code: string;
  name: string;
  archetype: string;
  centroid_lon: number;
  centroid_lat: number;
  area_km2: number;
  built_up_density: number;
  green_space_pct: number;
  water_body_pct: number;
  road_density_km_per_km2: number;
  building_height_mean_m: number;
  albedo_base: number;
  population_density_per_km2: number;
  population_total: number;
  vulnerable_population_pct: number;
}

export interface WardGeoJSON {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: { type: "Polygon"; coordinates: number[][][] };
    properties: {
      id: string;
      ward_code: string;
      name: string;
      archetype: string;
      built_up_density: number;
      green_space_pct: number;
      water_body_pct: number;
      population_total: number;
    };
  }>;
}

export interface DashboardSummary {
  city_id: string;
  city_name: string;
  generated_at: string;
  avg_lst: number;
  max_lst: number;
  hotspot_count: number;
  population_exposed: number;
  high_risk_ward_count: number;
  avg_vegetation_pct: number;
  avg_built_up_pct: number;
  is_demo: boolean;
  model_version: string;
}

export interface Hotspot {
  id: string;
  ward_id: string;
  ward_name: string;
  detected_on: string;
  lst_celsius: number;
  lst_lower: number;
  lst_upper: number;
  heat_score: number;
  risk_level: RiskLevel;
  confidence: number;
  rank_in_city: number | null;
  centroid_lon: number;
  centroid_lat: number;
}

export interface DriverContribution {
  feature: string;
  label: string;
  value: number;
  shap_value: number;
  direction: "increases_heat" | "decreases_heat";
  relative_contribution_pct: number;
}

export interface DriverAnalysis {
  ward_id: string;
  ward_name: string;
  lst_celsius: number;
  base_value: number;
  drivers: DriverContribution[];
  narrative: string;
}

export interface PredictionPoint {
  horizon_days: number;
  target_date: string;
  predicted_lst: number;
  predicted_lst_lower: number;
  predicted_lst_upper: number;
  change_from_current_c: number;
  risk_level: RiskLevel;
  confidence: number;
  physics_estimate_lst: number;
  disclaimer: string;
}

export interface PredictionResponse {
  ward_id: string;
  ward_name: string;
  as_of: string;
  current_lst: number;
  points: PredictionPoint[];
}

export interface WardComparisonRow {
  ward_id: string;
  ward_name: string;
  archetype: string;
  lst_celsius: number;
  heat_score: number;
  risk_level: RiskLevel;
  green_space_pct: number;
  built_up_density: number;
  population_total: number;
}

export interface InterventionCatalogItem {
  type: InterventionType;
  label: string;
  description: string;
  unit_cost_usd_per_pct_per_km2: number;
  land_fraction_of_coverage: number;
  water_m3_per_year_per_pct_per_km2: number;
  max_coverage_pct: number;
}

export interface InterventionInput {
  type: InterventionType;
  coverage_pct: number;
}

export interface ResourceBreakdownItem {
  type: string;
  label: string;
  coverage_pct: number;
  cost_usd: number;
  land_km2: number;
  water_m3_per_year: number;
}

export interface SimulationResult {
  id: string;
  ward_id: string;
  ward_name: string;
  interventions: InterventionInput[];
  baseline_lst: number;
  simulated_lst: number;
  expected_cooling_c: number;
  cooling_ci_low: number;
  cooling_ci_high: number;
  confidence: number;
  baseline_risk: RiskLevel;
  simulated_risk: RiskLevel;
  risk_reduction_pct: number;
  cost_usd: number;
  land_km2: number;
  water_m3_per_year: number;
  population_benefited: number;
  resource_breakdown: ResourceBreakdownItem[];
}

export interface RankedIntervention {
  type: string;
  label: string;
  coverage_pct: number;
}

export interface RankedStrategy {
  rank: number;
  interventions: RankedIntervention[];
  score: number;
  expected_cooling_c: number;
  cooling_ci_low: number;
  cooling_ci_high: number;
  cost_usd: number;
  population_benefited: number;
  land_km2: number;
  water_m3_per_year: number;
  risk_reduction_pct: number;
  confidence: number;
  reason: string;
}

export interface OptimizationConstraintsInput {
  ward_id: string;
  budget_usd: number;
  land_km2: number;
  water_m3_per_year: number;
  target_cooling_c?: number | null;
  population_priority?: number;
  risk_priority?: number;
}

export interface OptimizationRun {
  id: string;
  ward_id: string;
  ward_name: string;
  constraints: OptimizationConstraintsInput;
  strategies: RankedStrategy[];
}

export interface Recommendation {
  id: string;
  ward_id: string;
  ward_name: string;
  rank: number;
  title: string;
  narrative_text: string;
  metrics: {
    expected_cooling_c: number;
    cost_usd: number;
    population_benefited: number;
    risk_reduction_pct: number;
    confidence: number;
  };
}

export interface ReportOut {
  id: string;
  title: string;
  status: "generating" | "ready" | "failed";
  ward_id: string | null;
  city_id: string | null;
  created_at: string;
  download_url: string | null;
}

export interface ProviderStatus {
  provider: string;
  is_demo: boolean;
}

export interface DataSourceStatus {
  satellite: ProviderStatus;
  weather: ProviderStatus;
  urban: ProviderStatus;
  population: ProviderStatus;
  all_demo: boolean;
  notes: string[];
  detection_model_version: string;
  detection_model_metrics: Record<string, number>;
  pinn_trained: boolean;
}

export interface SystemStatus {
  database_connected: boolean;
  city_count: number;
  ward_count: number;
  user_count: number;
  simulation_count: number;
  optimization_run_count: number;
  heat_map_count: number;
  model_runs: Array<{ model_name: string; version: string; metrics: Record<string, unknown> }>;
  data_sources: DataSourceStatus;
}

export interface AuditLogEntry {
  id: string;
  created_at: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
}
