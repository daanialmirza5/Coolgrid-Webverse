import { cn } from "@/lib/utils";
import { RISK_BADGE_CLASS } from "@/lib/colors";
import type { RiskLevel } from "@/lib/types";

export function RiskBadge({ risk, className }: { risk: RiskLevel; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", RISK_BADGE_CLASS[risk], className)}>
      {risk}
    </span>
  );
}
