import { Suspense } from "react";
import { AlertCircle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getEmployees } from "@/lib/api";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { EmployeeTable } from "./employee-table";
import Loading from "./loading";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Mitarbeiter · Schichtplanung" };

export default async function EmployeesPage({ searchParams }: { searchParams: Promise<ScopeSearchParams> }) {
  const scope = await loadPlanningScope("/employees", await searchParams);
  return (
    <div className="py-6">
      <PageHeader
        title="Mitarbeiter"
        parent={{ href: "/", label: "Übersicht" }}
        description="Mitarbeiter der gewählten Stationen und des zugehörigen Pools, nur lesend."
        scope={scope}
      />
      {!scope.stationIds.length ? (
        <p className="py-12 text-center text-muted-foreground">Bitte mindestens eine Station auswählen.</p>
      ) : scope.error ? (
        <LoadError message={scope.error} />
      ) : (
        // A new key per scope shows the loading state instead of the previous scope's employees.
        <Suspense key={`${scope.month}:${scope.stationIds}`} fallback={<Loading />}>
          <Employees month={scope.month} stationIds={scope.stationIds} />
        </Suspense>
      )}
    </div>
  );
}

async function Employees({ month, stationIds }: { month: string; stationIds: number[] }) {
  const result = await getEmployees(month, stationIds).then(
    (inspection) => ({ inspection }),
    (error: Error) => ({ error: error.message }),
  );
  return "error" in result ? <LoadError message={result.error} /> : <EmployeeTable inspection={result.inspection} />;
}

function LoadError({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Mitarbeiter nicht geladen</AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        <p>Auswahl prüfen oder Stationen aktualisieren.</p>
      </AlertDescription>
    </Alert>
  );
}
