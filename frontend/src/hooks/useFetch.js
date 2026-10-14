import { useCallback, useEffect, useRef, useState } from "react";

// Generic data-fetch hook.
// fetcher: async function returning data (e.g. () => api.get("/api/buildings"))
// Returns { data, loading, error, refetch, setData }
export default function useFetch(fetcher, deps, opts) {
  const d = deps || [];
  const initial = (opts && opts.initial) || null;
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  // Join deps + tick into a stable key string
  const key = JSON.stringify(d) + ":" + tick;
  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetcher();
        if (!cancelled && mounted.current) setData(result);
      } catch (e) {
        if (!cancelled && mounted.current) setError(e);
      } finally {
        if (!cancelled && mounted.current) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { data, loading, error, refetch, setData };
}
