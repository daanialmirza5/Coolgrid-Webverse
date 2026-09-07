import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 p-10 text-center dark:border-slate-700", className)}>
      {Icon && <Icon className="h-8 w-8 text-slate-400" />}
      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{title}</p>
      {description && <p className="max-w-sm text-xs text-slate-500 dark:text-slate-400">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950">
      <p className="text-sm font-medium text-red-800 dark:text-red-300">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-xs font-semibold text-red-700 underline dark:text-red-300">
          Retry
        </button>
      )}
    </div>
  );
}
