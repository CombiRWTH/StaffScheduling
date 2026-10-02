import { BulletList } from "@/components/bullet-list";
import { Disclosure } from "@/components/disclosure";
import { Facts } from "@/components/facts";
import { ProblemBox } from "@/components/problem-box";
import { StatusLine, type Tone } from "@/components/status-line";
import { Card, CardContent } from "@/components/ui/card";
import {
  CHECK_STATUS,
  RULES,
  STAFF_LEVEL_LABELS,
  WISH_LABELS,
  WISH_STATUS_LABELS,
  missingInputs,
  formatDate,
  OBJECTIVE_LABELS,
  formatHours,
  formatSearchTime,
  formatStage,
  monthLabel,
  solverStatusText,
} from "@/lib/labels";
import type { CheckStatus, ScheduleReview } from "@/lib/types";

const SOURCES: Record<ScheduleReview["source"], string> = { generation: "Generiert", import: "Importiert" };
const TIME = new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" });
const TONES: Record<CheckStatus, Tone> = { accepted: "success", rejected: "error", incomplete: "warning" };

/**
 * What a staff admin needs about the schedule under review: its scope, whether it may be used, why not, and the
 * actions. How the solver got there sits in a collapsed technical section.
 */
export function ReviewSummary({ review, actions }: { review: ScheduleReview; actions: React.ReactNode }) {
  const { solution, tables } = review;
  const { check, configuration } = solution;
  const period = monthLabel(review.planning_month.year, review.planning_month.month);
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  const unitName = new Map(review.planning_units.map((unit) => [unit.planning_unit_id, unit.display_name]));
  const employeeName = new Map(tables.employees.map((row) => [row.employee_id, row.employee_name]));
  const shiftCode = new Map(review.shifts.map((shift) => [shift.shift_id, shift.code]));
  const [checkValue, checkDetail] = CHECK_STATUS[check.status];
  const publishable = check.status === "accepted" && tables.duties.length > 0;
  const missing = tables.gaps.reduce((total, row) => total + row.missing_count, 0);
  const hint = publishable
    ? missing > 0
      ? "Kann veröffentlicht werden; Lücken werden nicht veröffentlicht"
      : "Kann veröffentlicht werden"
    : check.status === "accepted"
      ? "Ohne Dienste nicht veröffentlichbar"
      : checkDetail;

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
  const inputs = missingInputs(check);

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
            <StatusLine tone={TONES[check.status]} title={checkValue} hint={hint} />
          </div>
          {actions}
        </div>

        <ProblemBox
          sections={[
            ["Verstöße", findings],
            ["Fehlende Eingaben", inputs.missing],
          ]}
        />

        {missing > 0 && (
          <section aria-label="Lücken" className="space-y-1.5 rounded-lg border border-amber-500/40 bg-amber-500/5 p-4">
            <p className="font-medium text-amber-800">
              {missing} {missing === 1 ? "unbesetzte Pflichtstelle" : "unbesetzte Pflichtstellen"} (Lücken)
            </p>
            <p className="text-muted-foreground">
              Kein einsetzbarer Mitarbeiter ist frei; für diese Schichten Gastpersonal anfragen.
            </p>
            <div className="max-h-64 overflow-y-auto">
              <BulletList
                items={tables.gaps.map(
                  (row) =>
                    `${formatDate(row.date)} · ${row.planning_unit_name} · ${row.shift_code} · ${STAFF_LEVEL_LABELS[row.staff_level]}: ${row.missing_count} von ${row.required_count} fehlen`,
                )}
              />
            </div>
          </section>
        )}

        {check.wishes.length > 0 && (
          <section aria-label="Wünsche" className="space-y-1.5">
            <p className="font-medium">
              Wünsche: {check.wish_counts.granted} erfüllt · {check.wish_counts.denied} nicht erfüllt ·{" "}
              {check.wish_counts.not_grantable} nicht erfüllbar
            </p>
            <p className="text-muted-foreground">
              Wünsche binden nicht; nicht erfüllbare widersprechen einer Verfügbarkeit oder Zuordnung.
            </p>
            <div className="max-h-64 overflow-y-auto">
              <BulletList
                items={check.wishes.map(
                  (row) =>
                    [
                      formatDate(row.date),
                      employeeName.get(row.employee_id) ?? `Mitarbeiter ${row.employee_id}`,
                      [WISH_LABELS[row.type], row.shift_id !== null && shiftCode.get(row.shift_id)]
                        .filter(Boolean)
                        .join(" "),
                    ].join(" · ") + `: ${WISH_STATUS_LABELS[row.status]}`,
                )}
              />
            </div>
          </section>
        )}

        <Disclosure title="Technische Details">
          <div className="grid gap-6 md:grid-cols-2">
            <Facts
              title="Solver"
              facts={[
                ["Status", solverStatusText(solution.status)],
                ["Suchzeit", formatSearchTime(solution.wall_time_seconds, configuration.timeout_seconds)],
                [
                  "Suchthreads",
                  configuration.search_workers === null ? "automatisch" : String(configuration.search_workers),
                ],
                ["Startwert", configuration.random_seed === null ? "keiner" : String(configuration.random_seed)],
                ...solution.stages.map((stage, index): [string, string] => [
                  `Stufe ${index + 1}: ${OBJECTIVE_LABELS[stage.name]}`,
                  formatStage(stage),
                ]),
              ]}
            />
            <Facts
              title="Bewertung"
              facts={[
                ["Lücken", String(check.scores.gaps)],
                [
                  "Gesundheitsereignisse",
                  `${check.scores.health_events} (${check.scores.six_day_windows} Sechs-Tage-Folgen, ${check.scores.backward_transitions} Rückwärtswechsel)`,
                ],
                ["Wunschkosten (Fairness)", String(check.scores.wish_cost)],
                ["Abweichung der Monatskonten", formatHours(check.scores.balance_deviation_minutes)],
                ["Überzählige Zwischendienste", String(check.scores.surplus_intermediate_duties)],
              ]}
            />
          </div>
          {inputs.later.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-muted-foreground">Über den Monat hinaus, hier nicht bewertet</p>
              <BulletList items={inputs.later} />
            </div>
          )}
          {solution.diagnostics.length > 0 && (
            <Facts
              title="Solver-Diagnosen"
              facts={solution.diagnostics.map((row, index) => [
                `${index + 1}. ${row.severity} ${row.code}`,
                row.message,
              ])}
            />
          )}
        </Disclosure>
      </CardContent>
    </Card>
  );
}
