import { Info, LoaderCircle } from "lucide-react";
import { BulletList } from "@/components/bullet-list";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { monthLabel } from "@/lib/labels";
import type { CheckStatus, GenerationJob, PlanningUnit, Rule, ScheduleCheck, SolutionStatus } from "@/lib/types";
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

/** The independent schedule check, apart from the solver status. */
const CHECK_STATUS: Record<CheckStatus, [string, string]> = {
  accepted: ["Regeln eingehalten", "Alle geprüften Regeln erfüllt"],
  rejected: ["Regelverstöße", "Der Plan ist nicht verwendbar"],
  incomplete: ["Unvollständig geprüft", "Für eine Regel fehlen Eingaben"],
};

/** German names of the checked rules, as the backend reports them. */
const RULES: Record<Rule, string> = {
  input: "Ungültige Dienste",
  staffing: "Mindestbesetzung",
  eligibility: "Zuordnung und Qualifikation",
  one_duty_per_day: "Ein Dienst pro Tag",
  availability: "Verfügbarkeit",
  monthly_balance: "Monatskonto",
  work_and_breaks: "Arbeitszeit und Pausen",
  work_average: "Durchschnittliche Arbeitszeit",
  rest: "Ruhezeit",
  consecutive_nights: "Nächte in Folge",
  night_recovery: "Erholung nach Nachtdiensten",
  replacement_rest: "Ersatzruhetag",
  annual_free_sundays: "Freie Sonntage im Jahr",
};

/** Count per rule, e.g. "Ruhezeit: 2". */
function perRule(rows: { rule: Rule }[]) {
  const counts = new Map<Rule, number>();
  for (const row of rows) counts.set(row.rule, (counts.get(row.rule) ?? 0) + 1);
  return [...counts].map(([rule, count]) => `${RULES[rule]}: ${count}`);
}

function checkOutcome(check: ScheduleCheck | null | undefined, running: boolean): [string, string, string?] {
  if (!check)
    return running
      ? ["Wartet auf Plan", "Prüft jeden gefundenen Plan"]
      : ["Kein Plan zu prüfen", "Ohne Lösung keine Prüfung"];
  const [value, detail] = CHECK_STATUS[check.status];
  return [value, detail, check.status === "accepted" ? undefined : "text-destructive"];
}

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
  const check = solution?.check;
  const [checkValue, checkDetail, checkTone] = checkOutcome(check, job.state === "running");
  const open = check?.not_assessed.filter((row) => !row.blocking) ?? [];
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
          <Outcome label="Prüfung" value={checkValue} detail={checkDetail} tone={checkTone} />
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
              ["Regelverstöße", check?.findings.length ?? 0],
              ["Nicht bewertet", check?.not_assessed.length ?? 0],
            ].map(([label, count]) => (
              <div key={label} className="flex items-baseline gap-2">
                <dd className="text-lg font-semibold tabular-nums">{count}</dd>
                <dt className="text-muted-foreground">{label}</dt>
              </div>
            ))}
          </dl>
        )}

        {check && (check.findings.length > 0 || check.not_assessed.length > 0) && (
          <div className="grid gap-4 text-sm sm:grid-cols-2">
            {check.findings.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-muted-foreground">Verstöße</p>
                <BulletList items={perRule(check.findings)} />
              </div>
            )}
            <div className="space-y-1.5">
              <p className="text-muted-foreground">Nicht bewertet</p>
              <BulletList
                items={[
                  ...perRule(check.not_assessed.filter((row) => row.blocking)).map(
                    (item) => `${item} (fehlende Eingaben)`,
                  ),
                  ...perRule(open).map((item) => `${item} (über den Monat hinaus)`),
                ]}
              />
            </div>
          </div>
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
