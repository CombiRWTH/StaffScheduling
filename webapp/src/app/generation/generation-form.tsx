"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { generate } from "./actions";

/** Solver time limit and start button; the job itself is shown by the page. */
export function GenerationForm({
  month,
  stationIds,
  running,
}: {
  month: string;
  stationIds: number[];
  running: boolean;
}) {
  const [timeoutSeconds, setTimeoutSeconds] = useState("30");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function start() {
    setError(null);
    startTransition(async () => {
      const result = await generate(month, stationIds, Number(timeoutSeconds));
      if (!result.ok) setError(`${result.error} Es wurde keine Generierung gestartet.`);
    });
  }

  return (
    <div className="space-y-4 border-t pt-6">
      <div className="space-y-2">
        <Label htmlFor="generation-timeout">Maximale Laufzeit (Sekunden)</Label>
        <Input
          id="generation-timeout"
          type="number"
          min={1}
          max={3600}
          value={timeoutSeconds}
          onChange={(event) => setTimeoutSeconds(event.target.value)}
          aria-describedby="generation-timeout-hint"
        />
        <p id="generation-timeout-hint" className="text-xs text-muted-foreground">
          Suchzeit des Solvers, 1–3600. Das Laden der Daten kommt hinzu.
        </p>
      </div>
      <Button className="w-full" disabled={pending || running || stationIds.length === 0} onClick={start}>
        {pending ? "Eingaben werden geprüft …" : "Generierung starten"}
      </Button>
      {running && (
        <p className="text-sm text-muted-foreground">Eine neue Generierung ist nach dem laufenden Job möglich.</p>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
