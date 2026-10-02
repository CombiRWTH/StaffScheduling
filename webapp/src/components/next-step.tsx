import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { PlanningScope } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";
import { steps } from "@/lib/steps";

/** Every step but the last; the review ends the sequence with its own actions. */
type StepWithNext = Exclude<(typeof steps)[number]["href"], "/review">;

/** A link to the step after the page's own one, keeping the selection. */
export function NextStep({ after, scope }: { after: StepWithNext; scope: PlanningScope }) {
  const index = steps.findIndex((step) => step.href === after);
  const next = steps[index + 1];
  return (
    <div className="mt-6 flex justify-end border-t pt-4">
      <Link
        href={`${next.href}${selectionSearch(scope.month, scope.stationIds)}`}
        className="inline-flex items-center gap-1 rounded-md font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        Weiter mit Schritt {index + 2}: {next.title}
        <ChevronRight className="size-4" aria-hidden />
      </Link>
    </div>
  );
}
