import Link from "next/link";
import { LoadError } from "@/components/load-error";
import { PageHeader } from "@/components/page-header";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getReview } from "@/lib/api";
import { monthLabel } from "@/lib/labels";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";
import type { ScheduleReview } from "@/lib/types";
import { AccountTable } from "./account-table";
import { ImportForm } from "./import-form";
import { ReviewSummary } from "./review-summary";
import { ScheduleGrid } from "./schedule-grid";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dienstplan prüfen · Schichtplanung" };

/** The review's month as `YYYY-MM` and its stations, for comparing with and linking to a selection. */
function reviewScope(review: ScheduleReview) {
  const { year, month } = review.planning_month;
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  return { month: `${year}-${String(month).padStart(2, "0")}`, stations };
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
  const matches =
    own &&
    own.month === scope.month &&
    own.stations.length === scope.stationIds.length &&
    own.stations.every((unit) => selected.has(unit.planning_unit_id));

  return (
    <div className="py-6">
      <PageHeader
        title="Dienstplan prüfen"
        parent={{ href: "/", label: "Übersicht" }}
        description="Den zuletzt generierten oder importierten Dienstplan prüfen und herunterladen."
        scope={scope}
      />
      <div className="space-y-6">
        {"error" in current && <LoadError title="Dienstplan nicht geladen" message={current.error} />}
        {"review" in current && !review && (
          <Card className="max-w-3xl border-dashed shadow-none">
            <CardHeader>
              <CardTitle>Kein Dienstplan zur Prüfung</CardTitle>
              <CardDescription>
                Einen Dienstplan generieren oder input.json und result.json importieren. Der Plan wird nur bis zum
                Neustart des Backends vorgehalten.
              </CardDescription>
            </CardHeader>
          </Card>
        )}
        {review && own && !matches && (
          <Card className="max-w-3xl">
            <CardHeader>
              <CardTitle>Anderer Planungsumfang</CardTitle>
              <CardDescription>
                Der Dienstplan zur Prüfung gehört zu{" "}
                {monthLabel(review.planning_month.year, review.planning_month.month).name} ·{" "}
                {own.stations.map((unit) => unit.display_name).join(", ")}.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link
                className={buttonVariants({ variant: "outline" })}
                href={`/review${selectionSearch(
                  own.month,
                  own.stations.map((unit) => unit.planning_unit_id),
                )}`}
              >
                Zu diesem Umfang wechseln
              </Link>
            </CardContent>
          </Card>
        )}
        {review && matches && (
          <>
            <ReviewSummary review={review} />
            <ScheduleGrid review={review} />
            <AccountTable review={review} />
          </>
        )}
        <ImportForm />
      </div>
    </div>
  );
}
