import { Suspense } from "react";
import LoadingEmployees from "./loading";
import { monthParams, readPlanningApi } from "@/features/planning/api";
import { PlanningInspectionSchema } from "@/features/planning/models";
import { EmployeesPageClient } from "./employees-page-client";

export default async function EmployeesPage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string; stations?: string }>;
}) {
  const { month, stations } = await searchParams;
  if (!month || !stations) return <p>Bitte einen Planungsmonat und mindestens eine Station auswählen.</p>;
  return (
    <Suspense key={`${month}:${stations}`} fallback={<LoadingEmployees />}>
      <EmployeeContent month={month} stations={stations} />
    </Suspense>
  );
}

async function EmployeeContent({ month, stations }: { month: string; stations: string }) {
  try {
    const params = monthParams(month);
    if (!/^[1-9]\d*(,[1-9]\d*)*$/.test(stations)) throw new Error("Bitte gültige Stationen auswählen.");
    for (const id of new Set(stations.split(","))) params.append("planning_unit_ids", id);
    const inspection = await readPlanningApi("/employees", params, PlanningInspectionSchema);
    const ids = [...new Set(stations.split(",").map(Number))];
    if (
      inspection.planning_month.start !== `${month}-01` ||
      ids.length !== inspection.selected_station_ids.length ||
      !ids.every((id) => inspection.selected_station_ids.includes(id))
    ) {
      throw new Error("Antwort gehört zu einer anderen Planungsauswahl. Bitte erneut laden.");
    }
    return <EmployeesPageClient key={`${month}:${stations}`} inspection={inspection} />;
  } catch (error) {
    return (
      <div role="alert" className="rounded-md border p-4">
        <h1 className="font-semibold">Mitarbeiter nicht geladen</h1>
        <p>{error instanceof Error ? error.message : "Daten nicht verfügbar."}</p>
        <p>Auswahl prüfen oder Stationen aktualisieren und erneut öffnen.</p>
      </div>
    );
  }
}
