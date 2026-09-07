import { heatColor, RISK_COLOR } from "@/lib/colors";
import type { MapLayerKey } from "@/lib/map-utils";

export function MapLegend({ activeLayer }: { activeLayer: MapLayerKey }) {
  if (activeLayer === "heat") {
    return (
      <LegendCard title="Land Surface Temperature">
        <GradientBar stops={[heatColor(0), heatColor(33), heatColor(66), heatColor(100)]} lowLabel="Cooler" highLabel="Hotter" />
      </LegendCard>
    );
  }
  if (activeLayer === "risk") {
    return (
      <LegendCard title="Heat Risk Level">
        <div className="flex flex-col gap-1.5">
          {(["LOW", "MODERATE", "HIGH", "CRITICAL"] as const).map((r) => (
            <div key={r} className="flex items-center gap-2 text-xs">
              <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: RISK_COLOR[r] }} />
              {r}
            </div>
          ))}
        </div>
      </LegendCard>
    );
  }
  if (activeLayer === "vegetation") {
    return (
      <LegendCard title="Vegetation Cover">
        <GradientBar stops={["#f1f5e9", "#166534"]} lowLabel="Low" highLabel="High" />
      </LegendCard>
    );
  }
  if (activeLayer === "built_up") {
    return (
      <LegendCard title="Built-up Density">
        <GradientBar stops={["#f1f5f9", "#334155"]} lowLabel="Low" highLabel="High" />
      </LegendCard>
    );
  }
  return (
    <LegendCard title="Population">
      <GradientBar stops={["#ede9fe", "#4c1d95"]} lowLabel="Low" highLabel="High" />
    </LegendCard>
  );
}

function LegendCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
      <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">{title}</p>
      {children}
    </div>
  );
}

function GradientBar({ stops, lowLabel, highLabel }: { stops: string[]; lowLabel: string; highLabel: string }) {
  return (
    <div className="w-40">
      <div className="h-2.5 w-full rounded-full" style={{ background: `linear-gradient(to right, ${stops.join(",")})` }} />
      <div className="mt-1 flex justify-between text-[10px] text-slate-500 dark:text-slate-400">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );
}
