import { CircleAlert, CircleCheck, CircleX } from "lucide-react";
import { BulletList } from "@/components/bullet-list";
import { Disclosure } from "@/components/disclosure";
import { Card, CardContent } from "@/components/ui/card";
import { CHECK_STATUS, RULES, SOLVER_STATUS, formatDate, formatHours, monthLabel } from "@/lib/labels";
import type { CheckStatus, ScheduleCheck, ScheduleReview } from "@/lib/types";
import { cn } from "@/lib/utils";

const SOURCES: Record<ScheduleReview["source"], string> = { generation: "Generiert", import: "Importiert" };
const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" });
const NUMBER = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 });
const STATUS_ICON: Record<CheckStatus, { icon: typeof CircleCheck; tone: string }> = {
  accepted: { icon: CircleCheck, tone: "text-green-700" },
  rejected: { icon: CircleX, tone: "text-destructive" },
  incomplete: { icon: CircleAlert, tone: "text-amber-700" },
};

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

const gapText = (row: ScheduleCheck["not_assessed"][number]) =>
  `${RULES[row.rule]} ${formatDate(row.start)}–${formatDate(row.end)}`;

/**
 * What a staff admin needs about the schedule under review: its scope, whether it may be used, why not, and the
 * actions. How the solver got there sits in a collapsed technical section.
 */
export function ReviewSummary({ review, actions }: { review: ScheduleReview; actions: React.ReactNode }) {
  const { solution, tables } = review;
  const { check, configuration, objective } = solution;
  const period = monthLabel(review.planning_month.year, review.planning_month.month);
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  const unitName = new Map(review.planning_units.map((unit) => [unit.planning_unit_id, unit.display_name]));
  const employeeName = new Map(tables.employees.map((row) => [row.employee_id, row.employee_name]));
  const [checkValue, checkDetail] = CHECK_STATUS[check.status];
  const [solverValue, solverDetail] = SOLVER_STATUS[solution.status];
  const { icon: StatusIcon, tone } = STATUS_ICON[check.status];

  const findings = check.findings.map((row) =>
    [
      `${RULES[row.rule]}: ${row.message}`,
      row.employee_id && employeeName.get(row.employee_id),
      row.date && formatDate(row.date),
      row.planning_unit_id && unitName.get(row.planning_unit_id),
    ]
      .filter(Boolean)
      .join(" · "),
  );
  const missing = check.not_assessed.filter((row) => row.blocking).map(gapText);
  const later = check.not_assessed.filter((row) => !row.blocking).map(gapText);

  return (
    <Card aria-label="Dienstplan zur Prüfung">
      <CardContent className="space-y-5 text-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">
              {period.name} · {stations.map((unit) => unit.display_name).join(", ")}
            </h2>
            <p className="text-muted-foreground">
              {SOURCES[review.source]} {TIME.format(new Date(review.received_at))} Uhr · {tables.duties.length} Dienste
            </p>
            <p className="pt-1">
              <StatusIcon className={cn("mr-1.5 inline size-4 align-[-3px]", tone)} aria-hidden />
              <span className={cn("font-medium", tone)}>{checkValue}</span>
              <span className="text-muted-foreground">
                {" · "}
                {check.status === "accepted" ? "Kann veröffentlicht werden" : checkDetail}
              </span>
            </p>
          </div>
          {actions}
        </div>

        {(findings.length > 0 || missing.length > 0) && (
          <div className="grid gap-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4 md:grid-cols-2">
            {findings.length > 0 && (
              <div className="space-y-1.5">
                <p className="font-medium">Verstöße</p>
                <div className="max-h-64 overflow-y-auto">
                  <BulletList items={findings} />
                </div>
              </div>
            )}
            {missing.length > 0 && (
              <div className="space-y-1.5">
                <p className="font-medium">Fehlende Eingaben</p>
                <BulletList items={missing} />
              </div>
            )}
          </div>
        )}

        <Disclosure title="Technische Details">
          <div className="grid gap-6 md:grid-cols-2">
            <Facts
              title="Solver"
              facts={[
                ["Status", `${solverValue} (${solverDetail})`],
                ["Optimalitätslücke", `${NUMBER.format(objective.relative_gap * 100)} % (keine fehlende Besetzung)`],
                ["Laufzeit", `${NUMBER.format(solution.wall_time_seconds)} von ${configuration.timeout_seconds} s`],
                [
                  "Suchthreads",
                  configuration.search_workers === null ? "automatisch" : String(configuration.search_workers),
                ],
                ["Startwert", configuration.random_seed === null ? "keiner" : String(configuration.random_seed)],
                [
                  "Gewichte",
                  `${configuration.weights.health_events} · ${configuration.weights.balance_deviation_minutes} · ${configuration.weights.surplus_intermediate_duties} (Gesundheit · Konten · Zwischendienste)`,
                ],
                ["Zielwert", String(objective.value)],
                ["Schranke", NUMBER.format(objective.best_bound)],
              ]}
            />
            <Facts
              title="Bewertung"
              facts={[
                [
                  "Gesundheitsereignisse",
                  `${check.scores.health_events} (${check.scores.six_day_windows} Sechs-Tage-Folgen, ${check.scores.backward_transitions} Rückwärtswechsel)`,
                ],
                ["Abweichung der Monatskonten", formatHours(check.scores.balance_deviation_minutes)],
                ["Überzählige Zwischendienste", String(check.scores.surplus_intermediate_duties)],
              ]}
            />
          </div>
          {later.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-muted-foreground">Über den Monat hinaus, hier nicht bewertet</p>
              <BulletList items={later} />
            </div>
          )}
          {solution.diagnostics.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-muted-foreground">Solver-Diagnosen</p>
              <BulletList items={solution.diagnostics.map((row) => row.message)} />
            </div>
          )}
        </Disclosure>
      </CardContent>
    </Card>
  );
}
