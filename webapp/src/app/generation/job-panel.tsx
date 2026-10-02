import Link from "next/link";
import { CircleAlert, CircleCheck, CircleX, LoaderCircle } from "lucide-react";
import { BulletList } from "@/components/bullet-list";
import { Disclosure } from "@/components/disclosure";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CHECK_STATUS, RULES, SOLVER_STATUS, monthLabel } from "@/lib/labels";
import { selectionMonth, selectionSearch } from "@/lib/selection";
import type { GenerationJob, PlanningUnit, Rule } from "@/lib/types";
import { cn } from "@/lib/utils";
import { RefreshWhileRunning } from "./refresh-while-running";

const STATES: Record<GenerationJob["state"], string> = {
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
};
const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", timeStyle: "medium" });
const NUMBER = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 });

type Tone = "busy" | "success" | "warning" | "error";
const TONES: Record<Tone, { icon: typeof CircleCheck; className: string }> = {
  busy: { icon: LoaderCircle, className: "text-foreground" },
  success: { icon: CircleCheck, className: "text-green-700" },
  warning: { icon: CircleAlert, className: "text-amber-700" },
  error: { icon: CircleX, className: "text-destructive" },
};

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
      hint: "Die Eingaben widersprechen sich. Die Hinweise nennen, wo die Mindestbesetzung nicht erreichbar ist.",
    };
  if (solution.status === "unknown")
    return {
      tone: "warning",
      title: "Keine Lösung innerhalb der Laufzeit",
      hint: "Mit einer längeren maximalen Laufzeit erneut starten.",
    };
  if (solution.status === "model_invalid")
    return { tone: "error", title: "Modell ungültig", hint: "Backend-Protokoll prüfen." };
  const status = solution.check?.status;
  if (status === "accepted")
    return {
      tone: "success",
      title: "Dienstplan erstellt, Regeln eingehalten",
      hint: "Jetzt prüfen und veröffentlichen; er wird nicht automatisch veröffentlicht.",
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
  const { tone, title, hint } = headline(job);
  const { icon: Icon, className } = TONES[tone];
  const times = `${TIME.format(new Date(job.started_at))} – ${
    job.finished_at ? TIME.format(new Date(job.finished_at)) : "…"
  } Uhr`;

  const facts: [string, string][] = [
    ["Ablauf", STATES[job.state]],
    ["Zeit", times],
    [
      "Solver",
      solution ? SOLVER_STATUS[solution.status][0] : job.state === "running" ? "Wird berechnet …" : "Kein Ergebnis",
    ],
    [
      "Prüfung",
      check ? CHECK_STATUS[check.status][0] : job.state === "running" ? "Wartet auf Plan" : "Kein Plan zu prüfen",
    ],
    ["Dienste", solution ? String(solution.assignments.length) : "–"],
  ];
  const blocking = check?.not_assessed.filter((row) => row.blocking) ?? [];
  const later = check?.not_assessed.filter((row) => !row.blocking) ?? [];
  const diagnostics = solution?.diagnostics ?? [];
  const hints = [
    ...diagnostics.filter((row) => row.severity !== "info").map((row) => row.message),
    ...perRule(check?.findings ?? []).map((item) => `Verstoß – ${item}`),
    ...perRule(blocking).map((item) => `${item} (fehlende Eingaben)`),
  ];

  return (
    <Card aria-label="Letzte Generierung">
      <CardContent className="space-y-4 text-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Letzte Generierung</h2>
            <p className="text-muted-foreground">
              {period.name} ({period.range}) · {stationIds.map(name).join(", ")}
            </p>
            <p className="pt-1">
              <Icon
                className={cn("mr-1.5 inline size-4 align-[-3px]", className, tone === "busy" && "animate-spin")}
                aria-hidden
              />
              <span className={cn("font-medium", className)}>{title}</span>
              <span className="text-muted-foreground"> · {hint}</span>
            </p>
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

        <dl className="grid gap-x-6 gap-y-2 rounded-lg border bg-muted/30 px-4 py-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
          {facts.map(([label, value]) => (
            <div key={label} className="min-w-0">
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>
          ))}
        </dl>

        {hints.length > 0 && (
          <div className="space-y-1.5 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
            <p className="font-medium">Hinweise</p>
            <BulletList items={hints} />
          </div>
        )}

        {(solution || job.state !== "running") && (
          <Disclosure title="Technische Details">
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
              {[
                ["Job", job.job_id],
                ["Solver-Status", solution ? SOLVER_STATUS[solution.status].join(" – ") : "Kein Ergebnis"],
                [
                  "Suchzeit",
                  solution
                    ? `${NUMBER.format(solution.wall_time_seconds)} von ${timeout_seconds} s`
                    : `bis ${timeout_seconds} s`,
                ],
                [
                  "Optimalitätslücke",
                  solution?.objective ? `${NUMBER.format(solution.objective.relative_gap * 100)} %` : "–",
                ],
                [
                  "Diagnosen",
                  diagnostics.length ? diagnostics.map((row) => `${row.severity} ${row.code}`).join(", ") : "keine",
                ],
              ].map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="break-all tabular-nums">{value}</dd>
                </div>
              ))}
            </dl>
            {later.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-muted-foreground">Nicht bewertet</p>
                <BulletList items={perRule(later).map((item) => `${item} (über den Monat hinaus)`)} />
              </div>
            )}
          </Disclosure>
        )}
        {job.state === "running" && <RefreshWhileRunning startedAt={job.started_at} timeoutSeconds={timeout_seconds} />}
      </CardContent>
    </Card>
  );
}
