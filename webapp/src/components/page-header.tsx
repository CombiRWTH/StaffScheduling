import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { PlanningScopePicker } from "@/components/planning-scope-picker";
import { Button } from "@/components/ui/button";
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
      <div className="flex items-start gap-2">
        {parent && (
          <Button variant="ghost" size="icon" className="mt-0.5 size-8 shrink-0" asChild>
            <Link
              href={`${parent.href}${selectionSearch(scope.month, scope.stationIds)}`}
              aria-label={`Zurück zu ${parent.label}`}
              title={`Zurück zu ${parent.label}`}
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
        )}
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="text-muted-foreground">{description}</p>
        </div>
      </div>
      <PlanningScopePicker {...scope} />
    </header>
  );
}
