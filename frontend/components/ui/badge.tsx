import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-transparent bg-sky-700 text-white",
        secondary: "border-transparent bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
        outline: "border-slate-300 text-slate-700 dark:border-slate-700 dark:text-slate-300",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  // A <span>, not a <div> -- badges commonly sit inside inline text (e.g. a
  // CardDescription <p>), where a block-level child is invalid HTML and
  // triggers a hydration mismatch warning.
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
