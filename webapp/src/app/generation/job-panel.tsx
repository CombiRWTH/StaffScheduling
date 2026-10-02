import { Info, LoaderCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { monthLabel } from "@/lib/labels";
import type { GenerationJob, PlanningUnit, SolutionStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { RefreshWhileRunning } from "./refresh-while-running";

const STATES: Record<GenerationJob["state"], string> = {
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
};

/** What the solver found, with a short explanation. */
const SOLVER_STATUS: Record<SolutionStatus, [string, string]> = {
  optimal: ["Optimale Lösung", "Bestmöglich nach den umgesetzten Regeln"],
  feasible: ["Lösung gefunden", "Optimum nicht nachgewiesen"],
  infeasible: ["Keine Lösung möglich", "Eingaben widersprechen sich"],
  unknown: ["Keine Lösung innerhalb der Laufzeit", "Längere Laufzeit versuchen"],
  model_invalid: ["Modell ungültig", "Backend-Protokoll prüfen"],
};

const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", timeStyle: "medium" });

/** One outcome of the job: a small label, the value and a muted explanation. */
function Outcome({
  label,
  value,
  detail,
  tone,
  busy,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
  busy?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={cn("mt-1 flex items-center gap-1.5 font-medium", tone)}>
        {busy && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
        {value}
      </p>
      <p className="mt-0.5 text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}

/** The latest job: its scope, and job progress, solver result and schedule check kept apart. */
export function JobPanel({ job, units }: { job: GenerationJob; units: PlanningUnit[] }) {
  const { planning_month: month, planning_unit_ids: stationIds, timeout_seconds } = job.request;
  const name = (id: number) => units.find((unit) => unit.planning_unit_id === id)?.display_name ?? `Station ${id}`;
  const solution = job.solution;
  const period = monthLabel(month.year, month.month);
  const [solverValue, solverDetail] = solution
    ? SOLVER_STATUS[solution.status]
    : job.state === "running"
      ? ["Wird berechnet …", `Laufzeit bis ${timeout_seconds} s`]
      : ["Kein Ergebnis", "Der Job ist fehlgeschlagen"];
  const times = `${TIME.format(new Date(job.started_at))} – ${
    job.finished_at ? TIME.format(new Date(job.finished_at)) : "…"
  } Uhr`;

  return (
    <Card aria-label="Letzte Generierung">
      <CardHeader>
        <CardTitle>Letzte Generierung</CardTitle>
        <CardDescription>
          {period.name} ({period.range}) · {stationIds.map(name).join(", ")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <Outcome
            label="Ablauf"
            value={STATES[job.state]}
            detail={times}
            tone={job.state === "failed" ? "text-destructive" : undefined}
            busy={job.state === "running"}
          />
          <Outcome label="Solver-Status" value={solverValue} detail={solverDetail} />
          <Outcome
            label="Prüfung"
            value="Noch nicht verfügbar"
            detail={solution?.assignments.length ? "Der Plan ist ein ungeprüfter Entwurf" : "Kein Plan zu prüfen"}
          />
        </div>

        {job.error && (
          <p className="text-sm text-destructive">
            Unerwarteter Fehler bei der Generierung. Details stehen im Backend-Protokoll.
          </p>
        )}
        {solution && (
          <dl className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
            {[
              ["Generierte Dienste", solution.assignments.length],
              ["Diagnosen", solution.diagnostics.length],
              ["Audit-Hinweise", solution.audit.findings.length],
            ].map(([label, count]) => (
              <div key={label} className="flex items-baseline gap-2">
                <dd className="text-lg font-semibold tabular-nums">{count}</dd>
                <dt className="text-muted-foreground">{label}</dt>
              </div>
            ))}
          </dl>
        )}

        <p className="flex items-center gap-2 border-t pt-4 text-sm text-muted-foreground">
          <Info className="size-4 shrink-0" />
          Das Ergebnis wird nicht automatisch veröffentlicht; die Generierung schreibt nichts nach TimeOffice.
        </p>
        {job.state === "running" && <RefreshWhileRunning startedAt={job.started_at} timeoutSeconds={timeout_seconds} />}
      </CardContent>
    </Card>
  );
}
