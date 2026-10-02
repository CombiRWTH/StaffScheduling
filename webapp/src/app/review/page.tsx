import Link from "next/link";
import { LoadError } from "@/components/load-error";
import { PageHeader } from "@/components/page-header";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { REVIEW_FILES, getReview } from "@/lib/api";
import { monthLabel } from "@/lib/labels";
import { loadPlanningScope, type PlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { selectionMonth, selectionSearch } from "@/lib/selection";
import type { ScheduleReview } from "@/lib/types";
import { AccountTable } from "./account-table";
import { ReviewActions } from "./review-actions";
import { ReviewSummary } from "./review-summary";
import { ScheduleGrid } from "./schedule-grid";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dienstplan prüfen · Schichtplan Manager" };

/** The review's month as `YYYY-MM` and its stations, for comparing with and linking to a selection. */
function reviewScope(review: ScheduleReview) {
  const { year, month } = review.planning_month;
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  return { month: selectionMonth(year, month), stations };
}

/** Whether the review's own scope is exactly the selected month and stations. */
function isSelected(own: ReturnType<typeof reviewScope>, scope: PlanningScope, selected: Set<number>) {
  return (
    own.month === scope.month &&
    own.stations.length === selected.size &&
    own.stations.every((unit) => selected.has(unit.planning_unit_id))
  );
}

/** The actions' scope: the selected stations and month, and the review if it is theirs. */
function publicationScope(scope: PlanningScope, selected: Set<number>, review: ScheduleReview | null) {
  const [year, month] = scope.month.split("-").map(Number);
  return {
    month: scope.month,
    monthName: monthLabel(year, month).name,
    stations: scope.stations
      .filter((unit) => selected.has(unit.planning_unit_id))
      .map((unit) => ({ id: unit.planning_unit_id, name: unit.display_name })),
    review: review && {
      receivedAt: review.received_at,
      duties: review.tables.duties.length,
      accepted: review.solution.check.status === "accepted",
    },
  };
}

export default async function ReviewPage({ searchParams }: { searchParams: Promise<ScopeSearchParams> }) {
  const params = await searchParams;
  const [scope, current] = await Promise.all([
    loadPlanningScope("/review", params),
    getReview().then(
      (review) => ({ review }),
      (error: Error) => ({ error: error.message }),
    ),
  ]);
  const review = "review" in current ? current.review : null;
  const own = review && reviewScope(review);
  const selected = new Set(scope.stationIds);
  const matches = own !== null && isSelected(own, scope, selected);
  const actions = (
    <ReviewActions {...publicationScope(scope, selected, matches ? review : null)} files={REVIEW_FILES} />
  );

  return (
    <div className="py-6">
      <PageHeader title="Dienstplan prüfen" parent={{ href: "/", label: "Übersicht" }} scope={scope} />
      <div className="space-y-6">
        {"error" in current && <LoadError title="Dienstplan nicht geladen" message={current.error} />}
        {review && matches ? (
          <>
            <ReviewSummary review={review} actions={actions} />
            <ScheduleGrid review={review} />
            <AccountTable review={review} />
          </>
        ) : (
          <Card className={review ? undefined : "border-dashed shadow-none"}>
            <CardContent className="flex flex-wrap items-start justify-between gap-4 text-sm">
              {review && own ? (
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold">Anderer Planungsumfang</h2>
                  <p className="text-muted-foreground">
                    Der Dienstplan zur Prüfung gehört zu{" "}
                    {monthLabel(review.planning_month.year, review.planning_month.month).name} ·{" "}
                    {own.stations.map((unit) => unit.display_name).join(", ")}.
                  </p>
                  <Link
                    className={buttonVariants({ variant: "outline" })}
                    href={`/review${selectionSearch(
                      own.month,
                      own.stations.map((unit) => unit.planning_unit_id),
                    )}`}
                  >
                    Zu diesem Umfang wechseln
                  </Link>
                </div>
              ) : (
                <div className="space-y-1">
                  <h2 className="text-lg font-semibold">Kein Dienstplan zur Prüfung</h2>
                  <p className="text-muted-foreground">
                    Einen Dienstplan generieren oder input.json und result.json importieren. Der Plan wird nur bis zum
                    Neustart des Backends vorgehalten.
                  </p>
                </div>
              )}
              {actions}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
