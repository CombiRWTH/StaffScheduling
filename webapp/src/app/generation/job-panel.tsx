import Link from "next/link";
import { BulletList } from "@/components/bullet-list";
import { Disclosure } from "@/components/disclosure";
import { Facts } from "@/components/facts";
import { ProblemBox } from "@/components/problem-box";
import { StatusLine, type Tone } from "@/components/status-line";
import { buttonVariants } from "@/components/ui/button-variants";
import { Card, CardContent } from "@/components/ui/card";
import {
  CHECK_STATUS,
  RULES,
  SOLVER_STATUS,
  checkGaps,
  diagnosticHints,
  formatSearchTime,
  formatStages,
  monthLabel,
  solverStatusText,
} from "@/lib/labels";
import { selectionMonth, selectionSearch } from "@/lib/selection";
import type { GenerationJob, PlanningUnit, Rule } from "@/lib/types";
import { RefreshWhileRunning } from "./refresh-while-running";

const STATES: Record<GenerationJob["state"], string> = {
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
};
const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", timeStyle: "medium" });

/** Count per rule, e.g. "Ruhezeit: 2". */
function perRule(rows: { rule: Rule }[]) {
  const counts = new Map<Rule, number>();
  for (const row of rows) counts.set(row.rule, (counts.get(row.rule) ?? 0) + 1);
  return [...counts].map(([rule, count]) => `${RULES[rule]}: ${count}`);
}

/** The outcome in one sentence a staff admin can act on, and what to do next. */
function headline(job: GenerationJob): { tone: Tone; title: string; hint: string } {
  const { solution } = job;
  if (job.state === "running")
    return {
      tone: "busy",
      title: "Dienstplan wird berechnet …",
      hint: `Bis zu ${job.request.timeout_seconds} s Suchzeit; die Seite aktualisiert sich selbst.`,
    };
  if (job.state === "failed" || !solution)
    return {
      tone: "error",
      title: "Generierung fehlgeschlagen",
      hint: "Unerwarteter Fehler bei der Generierung. Details stehen im Backend-Protokoll.",
    };
  if (solution.status === "infeasible")
    return {
      tone: "error",
      title: "Kein Dienstplan möglich",
      hint: "Die Eingaben widersprechen sich; die Hinweise nennen, was nicht erreichbar ist.",
    };
  if (solution.status === "unknown" || solution.status === "model_invalid")
    return {
      tone: solution.status === "unknown" ? "warning" : "error",
      title: SOLVER_STATUS[solution.status][0],
      hint: `${SOLVER_STATUS[solution.status][1]}.`,
    };
  const status = solution.check?.status;
  if (status === "accepted")
    return {
      tone: "success",
      title: "Dienstplan erstellt, Regeln eingehalten",
      hint: solution.assignments.length
        ? "Jetzt prüfen und veröffentlichen; er wird nicht automatisch veröffentlicht."
        : "Er enthält keine Dienste und kann nicht veröffentlicht werden.",
    };
  if (status === "incomplete")
    return {
      tone: "warning",
      title: "Dienstplan erstellt, aber unvollständig geprüft",
      hint: "Für eine Regel fehlen Eingaben, siehe Hinweise. Nicht veröffentlichbar.",
    };
  return {
    tone: "error",
    title: "Dienstplan erstellt, aber mit Regelverstößen",
    hint: "Nicht verwendbar; die Hinweise nennen die verletzten Regeln.",
  };
}

/** The fact row both audiences read: progress, time, solver, check and duty count. */
function jobFacts(job: GenerationJob): [string, string][] {
  const { solution } = job;
  const running = job.state === "running";
  const check = solution?.check;
  const end = job.finished_at ? TIME.format(new Date(job.finished_at)) : "…";
  return [
    ["Ablauf", STATES[job.state]],
    ["Zeit", `${TIME.format(new Date(job.started_at))} – ${end} Uhr`],
    ["Solver", solution ? SOLVER_STATUS[solution.status][0] : running ? "Wird berechnet …" : "Kein Ergebnis"],
    ["Prüfung", check ? CHECK_STATUS[check.status][0] : running ? "Wartet auf Plan" : "Kein Plan zu prüfen"],
    ["Dienste", solution ? String(solution.assignments.length) : "–"],
  ];
}

/** Solver internals for diagnosing a run; developers read the backend's own codes and messages here. */
function technicalFacts(job: GenerationJob): [string, string][] {
  const { solution } = job;
  const limit = job.request.timeout_seconds;
  return [
    ["Job-ID", job.job_id],
    ["Solver-Status", solution ? solverStatusText(solution.status) : "Kein Ergebnis"],
    ["Suchzeit", solution ? formatSearchTime(solution.wall_time_seconds, limit) : `bis ${limit} s`],
    ["Zielstufen", formatStages(solution?.stages ?? [])],
  ];
}

/**
 * The latest job: one sentence on the outcome for the staff admin, a compact fact row, the hints that explain a
 * failed or unusable run, and the solver internals collapsed for diagnosis.
 */
export function JobPanel({ job, units }: { job: GenerationJob; units: PlanningUnit[] }) {
  const { planning_month: month, planning_unit_ids: stationIds, timeout_seconds } = job.request;
  const name = (id: number) => units.find((unit) => unit.planning_unit_id === id)?.display_name ?? `Station ${id}`;
  const { solution } = job;
  const check = solution?.check;
  const period = monthLabel(month.year, month.month);
  const gaps = checkGaps(check);
  const diagnostics = solution?.diagnostics ?? [];

  return (
    <Card aria-label="Letzte Generierung">
      <CardContent className="space-y-4 text-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Letzte Generierung</h2>
            <p className="text-muted-foreground">
              {period.name} ({period.range}) · {stationIds.map(name).join(", ")}
            </p>
            <StatusLine {...headline(job)} />
          </div>
          {check && (
            <Link
              className={buttonVariants({ variant: check.status === "accepted" ? "default" : "outline" })}
              href={`/review${selectionSearch(selectionMonth(month.year, month.month), stationIds)}`}
            >
              Dienstplan prüfen
            </Link>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 rounded-lg border bg-muted/30 px-4 py-3 sm:grid-cols-3 lg:grid-cols-5">
          {jobFacts(job).map(([label, value]) => (
            <div key={label} className="min-w-0">
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>
          ))}
        </dl>

        <ProblemBox
          sections={[
            ["Hinweise", diagnosticHints(diagnostics)],
            ["Verstöße", perRule(check?.findings ?? [])],
            ["Fehlende Eingaben", gaps.missing],
          ]}
        />

        {job.state !== "running" && (
          <Disclosure title="Technische Details">
            <Facts facts={technicalFacts(job)} />
            {diagnostics.length > 0 && (
              <Facts
                title="Solver-Diagnosen"
                facts={diagnostics.map((row, index) => [`${index + 1}. ${row.severity} ${row.code}`, row.message])}
              />
            )}
            {gaps.later.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-muted-foreground">Über den Monat hinaus, hier nicht bewertet</p>
                <BulletList items={gaps.later} />
              </div>
            )}
          </Disclosure>
        )}
        {job.state === "running" && <RefreshWhileRunning startedAt={job.started_at} timeoutSeconds={timeout_seconds} />}
      </CardContent>
    </Card>
  );
}
