import * as React from "react";
import { cn } from "@/lib/utils";

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100",
      className
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";

export { Select };
