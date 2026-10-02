"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { generate } from "./actions";

// The API accepts solver time limits in this range (GenerationRequest).
const MIN_SECONDS = 30;
const MAX_SECONDS = 3600;

/** The scope to generate, the solver time limit and the start button in one row; the job is shown by the page. */
export function GenerationForm({
  month,
  stationIds,
  running,
  scope,
}: {
  month: string;
  stationIds: number[];
  running: boolean;
  scope: React.ReactNode;
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
    <div className="space-y-2">
      <div className="flex flex-wrap items-end justify-between gap-4">
        {scope}
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <Label htmlFor="generation-timeout" className="text-xs font-normal text-muted-foreground">
              Maximale Laufzeit
            </Label>
            <div className="relative">
              <Input
                id="generation-timeout"
                className="w-24 pr-7 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                type="number"
                min={MIN_SECONDS}
                max={MAX_SECONDS}
                value={timeoutSeconds}
                onChange={(event) => setTimeoutSeconds(event.target.value)}
                aria-describedby="generation-timeout-hint"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                s
              </span>
            </div>
          </div>
          <Button disabled={pending || running || stationIds.length === 0} onClick={start}>
            {pending ? "Eingaben werden geprüft …" : "Starten"}
          </Button>
        </div>
      </div>
      <p id="generation-timeout-hint" className="text-xs text-muted-foreground sm:text-right">
        Suchzeit des Solvers in Sekunden, {MIN_SECONDS}–{MAX_SECONDS}; das Laden der Daten kommt hinzu.
        {running && " Eine neue Generierung ist möglich, sobald die laufende beendet ist."}
      </p>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
