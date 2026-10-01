import { PlanningScopePicker } from "@/components/planning-scope-picker";
import type { PlanningScope } from "@/lib/scope";

export function PageHeader({
  title,
  description,
  scope,
}: {
  title: string;
  description: string;
  scope: PlanningScope;
}) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b pb-4">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-muted-foreground">{description}</p>
      </div>
      <PlanningScopePicker {...scope} />
    </header>
  );
}
