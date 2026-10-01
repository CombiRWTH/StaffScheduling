"use client";

import { Progress } from "@/components/ui/progress";
import type { SolverCommandType } from "@/entities/models/solver.model";

const PHASE_LABELS: Record<string, string> = {
  phase_1_upper_bound: "Obere Schranke berechnen…",
  phase_2_tight_bound: "Schranke präzisieren…",
  phase_3_optimizing: "Optimierung läuft…",
};

interface SolverProgressDisplayProps {
  progress: number;
  phase: string | null;
  isIndeterminate: boolean;
  runLabel: string | null;
  command: SolverCommandType;
  timeout: number;
}

export function SolverProgressDisplay({
  progress,
  phase,
  isIndeterminate,
  runLabel,
  command,
  timeout,
}: SolverProgressDisplayProps) {
  const isSolveCommand = command === "solve" || command === "solve-multiple";
  const isApiMode = phase !== null;
  const phaseLabel = isApiMode ? (PHASE_LABELS[phase] ?? "Berechnung läuft…") : "Berechnung läuft…";

  let footerText: string | null = null;
  if (isSolveCommand) {
    if (!isApiMode) {
      footerText =
        command === "solve"
          ? `Geschätzte Laufzeit: ${timeout}s`
          : `Geschätzte Laufzeit: ${timeout * 3}s (3× ${timeout}s)`;
    } else if (phase === "phase_3_optimizing") {
      footerText = `Timeout: ${timeout}s`;
    } else {
      footerText = "Phase 1 & 2 dauern typischerweise wenige Sekunden";
    }
  }

  return (
    <div className="p-4 bg-muted rounded-lg space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{isSolveCommand ? phaseLabel : "Der Befehl wird ausgeführt…"}</span>
        <div className="flex items-center gap-2">
          {runLabel && <span className="text-xs text-muted-foreground font-medium">{runLabel}</span>}
          <span className="text-muted-foreground font-mono">{progress.toFixed(0)}%</span>
        </div>
      </div>
      <div className={isIndeterminate ? "animate-pulse" : undefined}>
        <Progress value={progress} className="h-2" />
      </div>
      {footerText && <p className="text-xs text-center text-muted-foreground">{footerText}</p>}
    </div>
  );
}
