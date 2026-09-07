import * as React from "react";
import { cn } from "@/lib/utils";

export type SliderProps = React.InputHTMLAttributes<HTMLInputElement>;

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    type="range"
    className={cn(
      "h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-sky-700 dark:bg-slate-700",
      className
    )}
    {...props}
  />
));
Slider.displayName = "Slider";

export { Slider };
