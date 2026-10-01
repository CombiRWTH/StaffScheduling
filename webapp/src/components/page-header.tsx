import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { PlanningScopePicker } from "@/components/planning-scope-picker";
import type { PlanningScope } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";

/**
 * Title, description and planning selection of a page.
 * Every page below the overview passes `parent`, which renders a back link before the title
 * that keeps the current selection.
 */
export function PageHeader({
  title,
  description,
  scope,
  parent,
}: {
  title: string;
  description: string;
  scope: PlanningScope;
  parent?: { href: string; label: string };
}) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b pb-4">
      <div>
        <div className="flex items-center gap-1">
          {parent && (
            <Link
              href={`${parent.href}${selectionSearch(scope.month, scope.stationIds)}`}
              aria-label={`Zurück zu ${parent.label}`}
              title={`Zurück zu ${parent.label}`}
              className="-ml-1 rounded-md text-foreground transition-opacity hover:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <ChevronLeft className="size-6" strokeWidth={2.25} />
            </Link>
          )}
          <h1 className="text-2xl font-bold">{title}</h1>
        </div>
        <p className="text-muted-foreground">{description}</p>
      </div>
      <PlanningScopePicker {...scope} />
    </header>
  );
}
