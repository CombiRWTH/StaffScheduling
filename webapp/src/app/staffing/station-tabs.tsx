import Link from "next/link";
import { selectionSearch } from "@/lib/selection";
import { cn } from "@/lib/utils";
import type { PlanningUnit } from "@/lib/types";

/** One tab per selected station; the shown station lives in the URL next to the selection. */
export function StationTabs({
  month,
  stations,
  selectedId,
}: {
  month: string;
  stations: PlanningUnit[];
  selectedId: number;
}) {
  const search = selectionSearch(
    month,
    stations.map((station) => station.planning_unit_id),
  );
  return (
    <nav aria-label="Station" className="flex flex-wrap gap-1 border-b">
      {stations.map((station) => (
        <Link
          key={station.planning_unit_id}
          href={`/staffing${search}&station=${station.planning_unit_id}`}
          aria-current={station.planning_unit_id === selectedId ? "page" : undefined}
          className={cn(
            "-mb-px border-b-2 px-3 py-2 text-sm",
            station.planning_unit_id === selectedId
              ? "border-primary font-medium"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          {station.display_name}
        </Link>
      ))}
    </nav>
  );
}
