import { Suspense } from "react";
import { PageHeader } from "@/components/page-header";
import { LoadError } from "@/components/load-error";
import { getEmployeeCalendar, getPlanningEmployees } from "@/lib/api";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";
import { AvailabilityCalendar } from "./availability-calendar";
import { EmployeePicker } from "./employee-picker";
import Loading from "./loading";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Verfügbarkeit · Schichtplan Manager" };

export default async function AvailabilityPage({
  searchParams,
}: {
  searchParams: Promise<ScopeSearchParams & { employee?: string }>;
}) {
  const params = await searchParams;
  const scope = await loadPlanningScope("/availability", params);
  return (
    <div className="py-6">
      <PageHeader title="Verfügbarkeit" parent={{ href: "/", label: "Übersicht" }} scope={scope} />
      {!scope.stationIds.length ? (
        <p className="py-12 text-center text-muted-foreground">Bitte mindestens eine Station auswählen.</p>
      ) : scope.error ? (
        <LoadError title="Verfügbarkeit nicht geladen" message={scope.error} />
      ) : (
        // A new key per scope and employee shows the loading state instead of the previous calendar.
        <Suspense key={`${scope.month}:${scope.stationIds}:${params.employee}`} fallback={<Loading />}>
          <EmployeeAvailability month={scope.month} stationIds={scope.stationIds} employee={params.employee} />
        </Suspense>
      )}
    </div>
  );
}

async function EmployeeAvailability({
  month,
  stationIds,
  employee,
}: {
  month: string;
  stationIds: number[];
  employee?: string;
}) {
  let employees;
  try {
    employees = await getPlanningEmployees(month, stationIds);
  } catch (error) {
    return <LoadError title="Verfügbarkeit nicht geladen" message={(error as Error).message} />;
  }
  if (!employees.length) {
    return <p className="py-12 text-center text-muted-foreground">Keine Mitarbeiter in der Auswahl.</p>;
  }
  const selected = employees.find((row) => String(row.employee_id) === employee) ?? employees[0];
  const calendar = await getEmployeeCalendar(month, selected.employee_id).then(
    (result) => ({ result }),
    (error: Error) => ({ error: error.message }),
  );
  return (
    <div className="space-y-4">
      <EmployeePicker
        href={`/availability${selectionSearch(month, stationIds)}`}
        employees={employees}
        selectedId={selected.employee_id}
      />
      {"error" in calendar ? (
        <LoadError title="Verfügbarkeit nicht geladen" message={calendar.error} />
      ) : (
        // A new key per employee and month discards the previous editor state.
        <AvailabilityCalendar key={`${month}:${selected.employee_id}`} calendar={calendar.result} />
      )}
    </div>
  );
}
