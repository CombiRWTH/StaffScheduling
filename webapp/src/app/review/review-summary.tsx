import { Download, Info } from "lucide-react";
import { BulletList } from "@/components/bullet-list";
import { Outcome } from "@/components/outcome";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { REVIEW_FILES } from "@/lib/api";
import { CHECK_STATUS, RULES, SOLVER_STATUS, formatDate, monthLabel } from "@/lib/labels";
import type { ScheduleReview } from "@/lib/types";

const SOURCES: Record<ScheduleReview["source"], string> = { generation: "Generiert", import: "Importiert" };
const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" });
const NUMBER = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 });

/** A labelled list of facts, e.g. scores or settings. */
function Facts({ title, facts }: { title: string; facts: [string, string][] }) {
  return (
    <div className="space-y-1.5">
      <p className="text-muted-foreground">{title}</p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        {facts.map(([label, value]) => (
          <div key={label} className="contents">
            <dt>{label}</dt>
            <dd className="tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** Scope, solver result, independent check, scores, settings and downloads of the schedule under review. */
export function ReviewSummary({ review }: { review: ScheduleReview }) {
  const { solution, tables } = review;
  const { check, configuration, objective } = solution;
  const period = monthLabel(review.planning_month.year, review.planning_month.month);
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  const unitName = new Map(review.planning_units.map((unit) => [unit.planning_unit_id, unit.display_name]));
  const employeeName = new Map(tables.employees.map((row) => [row.employee_id, row.employee_name]));
  const [solverValue, solverDetail] = SOLVER_STATUS[solution.status];
  const [checkValue, checkDetail] = CHECK_STATUS[check.status];
  const accepted = check.status === "accepted";

  const findings = check.findings.map((row) =>
    [
      `${RULES[row.rule]}: ${row.message}`,
      row.employee_id && (employeeName.get(row.employee_id) ?? `Mitarbeiter ${row.employee_id}`),
      row.date && formatDate(row.date),
      row.planning_unit_id && unitName.get(row.planning_unit_id),
    ]
      .filter(Boolean)
      .join(" · "),
  );
  const notAssessed = check.not_assessed.map(
    (row) =>
      `${RULES[row.rule]} ${formatDate(row.start)}–${formatDate(row.end)} (${
        row.blocking ? "fehlende Eingaben, verhindert die Annahme" : "über den Monat hinaus"
      })`,
  );

  return (
    <Card aria-label="Dienstplan zur Prüfung" className="max-w-5xl">
      <CardHeader>
        <CardTitle>Dienstplan zur Prüfung</CardTitle>
        <CardDescription>
          {period.name} ({period.range}) · {stations.map((unit) => unit.display_name).join(", ")} ·{" "}
          {SOURCES[review.source]} {TIME.format(new Date(review.received_at))} Uhr
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 text-sm">
        <div className="grid gap-3 md:grid-cols-3">
          <Outcome label="Solver-Status" value={solverValue} detail={solverDetail} />
          <Outcome
            label="Prüfung"
            value={checkValue}
            detail={checkDetail}
            tone={accepted ? undefined : "text-destructive"}
          />
          <Outcome
            label="Zielfunktion"
            value={objective ? `Lücke ${NUMBER.format(objective.relative_gap * 100)} %` : "Nicht verfügbar"}
            detail={objective ? `Wert ${objective.value}, Schranke ${NUMBER.format(objective.best_bound)}` : ""}
          />
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Facts
            title="Bewertung"
            facts={[
              [
                "Gesundheitsereignisse",
                `${check.scores.health_events} (${check.scores.six_day_windows} Sechs-Tage-Folgen, ${check.scores.backward_transitions} Rückwärtswechsel)`,
              ],
              ["Abweichung der Monatskonten", `${check.scores.balance_deviation_minutes} min`],
              ["Überzählige Zwischendienste", String(check.scores.surplus_intermediate_duties)],
              ["Dienste", String(tables.duties.length)],
            ]}
          />
          <Facts
            title="Einstellungen"
            facts={[
              ["Laufzeit", `${NUMBER.format(solution.wall_time_seconds)} von ${configuration.timeout_seconds} s`],
              [
                "Suchthreads",
                configuration.search_workers === null ? "automatisch" : String(configuration.search_workers),
              ],
              ["Startwert", configuration.random_seed === null ? "keiner" : String(configuration.random_seed)],
              [
                "Gewichte",
                `${configuration.weights.health_events} · ${configuration.weights.balance_deviation_minutes} · ${configuration.weights.surplus_intermediate_duties}`,
              ],
            ]}
          />
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-1.5">
            <p className="text-muted-foreground">Verstöße</p>
            {findings.length ? (
              <div className="max-h-64 overflow-y-auto">
                <BulletList items={findings} />
              </div>
            ) : (
              <p>Keine</p>
            )}
          </div>
          <div className="space-y-1.5">
            <p className="text-muted-foreground">Nicht bewertet</p>
            <BulletList items={notAssessed} />
          </div>
        </div>

        {solution.diagnostics.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-muted-foreground">Solver-Diagnosen</p>
            <BulletList items={solution.diagnostics.map((row) => row.message)} />
          </div>
        )}

        <div className="space-y-2 border-t pt-4">
          <div className="flex flex-wrap gap-2">
            {REVIEW_FILES.map((name) => (
              <a key={name} href={`/review/files/${name}`} download className={buttonVariants({ variant: "outline" })}>
                <Download />
                {name}
              </a>
            ))}
          </div>
          <p className="flex items-center gap-2 text-muted-foreground">
            <Info className="size-4 shrink-0" />
            {accepted
              ? "Nicht veröffentlicht; die Dateien sind ohne TimeOffice lesbar und prüfbar."
              : "Nicht angenommen: Die Dateien sind eine Diagnose, kein verwendbarer Dienstplan."}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
