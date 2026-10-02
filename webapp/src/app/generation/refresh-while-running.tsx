"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const INTERVAL_MS = 2_000;
// Allowance beyond the solver's time limit for reading the model and extracting the result.
const MARGIN_MS = 60_000;

/** Re-render the page every two seconds while the job runs, until its time limit plus a margin has passed. */
export function RefreshWhileRunning({ startedAt, timeoutSeconds }: { startedAt: string; timeoutSeconds: number }) {
  const router = useRouter();
  const deadline = Date.parse(startedAt) + timeoutSeconds * 1000 + MARGIN_MS;
  const [overdue, setOverdue] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      if (Date.now() > deadline) {
        setOverdue(true);
        clearInterval(timer);
      } else {
        router.refresh();
      }
    }, INTERVAL_MS);
    return () => clearInterval(timer);
  }, [deadline, router]);

  return overdue ? (
    <p role="alert" className="text-sm text-destructive">
      Der Job läuft länger als erwartet. Seite neu laden; bleibt er hängen, Backend-Protokoll prüfen.
    </p>
  ) : null;
}
