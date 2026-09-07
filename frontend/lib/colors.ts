import type { RiskLevel } from "./types";

/**
 * Status palette (validated: contrast + CVD-safe adjacent pairs) reused for
 * both the categorical risk badges AND the continuous LST gradient on the
 * map, so a CRITICAL-red area on the map means exactly the same thing as a
 * CRITICAL badge everywhere else in the app.
 */
export const STATUS_COLORS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
} as const;

export const RISK_COLOR: Record<RiskLevel, string> = {
  LOW: STATUS_COLORS.good,
  MODERATE: STATUS_COLORS.warning,
  HIGH: STATUS_COLORS.serious,
  CRITICAL: STATUS_COLORS.critical,
};

export const RISK_BADGE_CLASS: Record<RiskLevel, string> = {
  LOW: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  MODERATE: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
  HIGH: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-800",
  CRITICAL: "bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
};

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgbToHex([r, g, b]: [number, number, number]): string {
  return "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

const HEAT_STOPS = [STATUS_COLORS.good, STATUS_COLORS.warning, STATUS_COLORS.serious, STATUS_COLORS.critical].map(
  hexToRgb
);

/** Continuous heat gradient (0-100 heat score) built from the same
 * good->warning->serious->critical anchors as the risk badges. */
export function heatColor(pct: number): string {
  const clamped = Math.max(0, Math.min(100, pct));
  const segment = clamped / 100 / (1 / (HEAT_STOPS.length - 1));
  const idx = Math.min(Math.floor(segment), HEAT_STOPS.length - 2);
  const t = segment - idx;
  const from = HEAT_STOPS[idx];
  const to = HEAT_STOPS[idx + 1];
  return rgbToHex([lerp(from[0], to[0], t), lerp(from[1], to[1], t), lerp(from[2], to[2], t)]);
}

export const SEQUENTIAL_BLUE = {
  100: "#cde2fb",
  200: "#9ec5f4",
  300: "#6da7ec",
  400: "#3987e5",
  500: "#256abf",
  600: "#184f95",
  700: "#0d366b",
};

export const CHART = {
  warms: STATUS_COLORS.critical,
  cools: STATUS_COLORS.good,
  primary: SEQUENTIAL_BLUE[500],
  band: "rgba(37, 106, 191, 0.15)",
  grid: "#e1e0d9",
  gridDark: "#2c2c2a",
  axis: "#898781",
};
