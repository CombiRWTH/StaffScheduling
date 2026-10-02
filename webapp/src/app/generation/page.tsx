import { BulletList } from "@/components/bullet-list";
import { LoadError } from "@/components/load-error";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { getLatestGeneration } from "@/lib/api";
import { selectionMonthLabel } from "@/lib/labels";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { GenerationForm } from "./generation-form";
import { JobPanel } from "./job-panel";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dienstplan erstellen · Schichtplan Manager" };

const USED = [
  "Mitarbeiter und Zuordnungen",
  "Monatskonten",
  "Abwesenheiten",
  "Einschränkungen",
  "Wünsche",
  "Mindestbesetzung",
  "Arbeitszeit-, Pausen- und Ruheregeln",
  "gesicherte Dienste vor und nach dem Monat",
];
const NOT_USED = ["bestehende Dienste im Dienstplan"];

export default async function GenerationPage({ searchParams }: { searchParams: Promise<ScopeSearchParams> }) {
  const params = await searchParams;
  const [scope, latest] = await Promise.all([
    loadPlanningScope("/generation", params),
    getLatestGeneration().then(
      (job) => ({ job }),
      (error: Error) => ({ error: error.message }),
    ),
  ]);
  const running = "job" in latest && latest.job?.state === "running";
  const selectedIds = new Set(scope.stationIds);
  const selected = scope.stations.filter((unit) => selectedIds.has(unit.planning_unit_id));
  const period = selectionMonthLabel(scope.month);

  return (
    <div className="py-6">
      <PageHeader title="Dienstplan erstellen" back scope={scope} />
      {scope.error && (
        <div className="mb-6">
          <LoadError title="Stationen nicht geladen" message={scope.error} />
        </div>
      )}

      <div className="space-y-6">
        <Card aria-label="Neue Generierung">
          <CardContent className="space-y-3 text-sm">
            <GenerationForm
              month={scope.month}
              stationIds={scope.stationIds}
              running={running}
              scope={
                <div className="space-y-1">
                  <h2 className="text-lg font-semibold">
                    {period.name}
                    {selected.length > 0 && <> · {selected.map((unit) => unit.display_name).join(", ")}</>}
                  </h2>
                  <p className="text-muted-foreground">
                    {selected.length ? `Ganzer Monat, ${period.range}` : "Bitte mindestens eine Station auswählen."}
                  </p>
                </div>
              }
            />
            <div className="grid gap-4 border-t pt-3 text-muted-foreground sm:grid-cols-2">
              <div className="space-y-1.5">
                <p className="font-medium text-foreground">Berücksichtigt</p>
                <BulletList items={USED} />
              </div>
              <div className="space-y-1.5">
                <p className="font-medium text-foreground">Nicht berücksichtigt</p>
                <BulletList items={NOT_USED} />
              </div>
            </div>
          </CardContent>
        </Card>

        {"error" in latest ? (
          <LoadError title="Generierung nicht geladen" message={latest.error} />
        ) : latest.job ? (
          <JobPanel job={latest.job} units={scope.stations} />
        ) : (
          <Card aria-label="Letzte Generierung" className="border-dashed shadow-none">
            <CardContent className="text-sm">
              <h2 className="text-lg font-semibold">Letzte Generierung</h2>
              <p className="text-muted-foreground">
                Kein Ergebnis verfügbar. Generierungen werden nur bis zum Neustart des Backends vorgehalten.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
