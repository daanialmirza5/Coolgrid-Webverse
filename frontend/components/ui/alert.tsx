import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const alertVariants = cva("relative w-full rounded-lg border px-4 py-3 text-sm", {
  variants: {
    variant: {
      default: "border-slate-200 bg-slate-50 text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200",
      destructive: "border-red-300 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300",
      warning: "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300",
      success: "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300",
    },
  },
  defaultVariants: { variant: "default" },
});

export function Alert({ className, variant, ...props }: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>) {
  return <div role="alert" className={cn(alertVariants({ variant, className }))} {...props} />;
}
