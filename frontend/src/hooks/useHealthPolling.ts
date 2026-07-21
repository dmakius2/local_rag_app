import { useEffect } from "react";
import { useHealthStore } from "@/context";

const POLL_INTERVAL_MS = 30_000;

/** Checks GET /health on mount and every POLL_INTERVAL_MS after, so the UI
 * can surface an "API unavailable" banner without the user issuing a request
 * first. */
export function useHealthPolling(): void {
  const check = useHealthStore((s) => s.check);

  useEffect(() => {
    console.log("HOOK: useHealthPolling() Running");
    check();
    const id = setInterval(check, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [check]);
}
