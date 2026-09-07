"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./api-client";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Generic client-side data-fetching hook: loading / success / error / retry
 * states for a promise-returning API call, re-run when `deps` change. */
export function useApi<T>(fn: () => Promise<T>, deps: React.DependencyList = []): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  useEffect(() => {
    fnRef.current = fn;
  });

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    // Resetting to a loading state when `deps`/`tick` change (a new request
    // is starting) is intentional here, not an accidental extra render --
    // this hook's entire contract is loading/success/error/retry for a
    // client-fetched API call.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);
    fnRef
      .current()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, loading, error, reload };
}
