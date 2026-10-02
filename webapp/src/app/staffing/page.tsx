import { PageHeader } from "@/components/page-header";
import { LoadError } from "@/components/load-error";
import { getDemand } from "@/lib/api";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { StaffingEditor } from "./staffing-editor";
import { StationTabs } from "./station-tabs";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Mindestbesetzung · Schichtplanung" };

export default async function StaffingPage({
  searchParams,
}: {
  searchParams: Promise<ScopeSearchParams & { station?: string }>;
}) {
  const params = await searchParams;
  const scope = await loadPlanningScope("/staffing", params);
  const stationId = scope.stationIds.find((id) => String(id) === params.station) ?? scope.stationIds[0];
  const selectedIds = new Set(scope.stationIds);
  const selected = scope.stations.filter((unit) => selectedIds.has(unit.planning_unit_id));
  return (
    <div className="py-6">
      <PageHeader
        title="Mindestbesetzung"
        parent={{ href: "/", label: "Übersicht" }}
        description="Mindestbesetzung je Tag, Schicht und Qualifikation für den Planungsmonat."
        scope={scope}
      />
      {!stationId ? (
        <p className="py-12 text-center text-muted-foreground">Bitte mindestens eine Station auswählen.</p>
      ) : scope.error ? (
        <LoadError title="Mindestbesetzung nicht geladen" message={scope.error} />
      ) : (
        <div className="space-y-4">
          <StationTabs month={scope.month} stations={selected} selectedId={stationId} />
          <StationDemand month={scope.month} stationId={stationId} />
        </div>
      )}
    </div>
  );
}

async function StationDemand({ month, stationId }: { month: string; stationId: number }) {
  const result = await getDemand(month, stationId).then(
    (configuration) => ({ configuration }),
    (error: Error) => ({ error: error.message }),
  );
  if ("error" in result) return <LoadError title="Mindestbesetzung nicht geladen" message={result.error} />;
  // A new key per station month discards unsaved edits of the previous one.
  return <StaffingEditor key={`${month}:${stationId}`} month={month} configuration={result.configuration} />;
}
