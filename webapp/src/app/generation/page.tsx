import { BulletList } from "@/components/bullet-list";
import { LoadError } from "@/components/load-error";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestGeneration } from "@/lib/api";
import { monthLabel } from "@/lib/labels";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { GenerationForm } from "./generation-form";
import { JobPanel } from "./job-panel";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dienstplan erstellen · Schichtplanung" };

const USED = [
  "Mitarbeiter und Zuordnungen",
  "Monatskonten",
  "Abwesenheiten",
  "Einschränkungen",
  "Mindestbesetzung",
  "Arbeitszeit-, Pausen- und Ruheregeln",
  "Gesicherte Dienste vor und nach dem Monat",
];
const NOT_USED = ["Wünsche", "Bestehende Dienste im Dienstplan"];

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
  const [year, month] = scope.month.split("-").map(Number);
  const period = monthLabel(year, month);

  return (
    <div className="py-6">
      <PageHeader
        title="Dienstplan erstellen"
        parent={{ href: "/", label: "Übersicht" }}
        description="Einen Dienstplan für den ganzen Planungsmonat und die gewählten Stationen generieren."
        scope={scope}
      />
      {scope.error && (
        <div className="mb-6">
          <LoadError title="Stationen nicht geladen" message={scope.error} />
        </div>
      )}

      <div className="max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Neue Generierung</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <dl className="grid gap-x-8 gap-y-5 text-sm sm:grid-cols-2">
              <div className="space-y-1">
                <dt className="text-muted-foreground">Zeitraum</dt>
                <dd className="font-medium">
                  {period.name} <span className="font-normal text-muted-foreground">({period.range})</span>
                </dd>
              </div>
              <div className="space-y-1">
                <dt className="text-muted-foreground">Stationen</dt>
                <dd className="flex flex-wrap gap-1.5">
                  {selected.length ? (
                    selected.map((unit) => (
                      <Badge key={unit.planning_unit_id} variant="secondary">
                        {unit.display_name}
                      </Badge>
                    ))
                  ) : (
                    <span>Bitte mindestens eine Station auswählen.</span>
                  )}
                </dd>
              </div>
              <div className="space-y-1.5">
                <dt className="text-muted-foreground">Berücksichtigt</dt>
                <dd>
                  <BulletList items={USED} />
                </dd>
              </div>
              <div className="space-y-1.5">
                <dt className="text-muted-foreground">Nicht berücksichtigt</dt>
                <dd>
                  <BulletList items={NOT_USED} />
                </dd>
              </div>
            </dl>
            <GenerationForm month={scope.month} stationIds={scope.stationIds} running={running} />
          </CardContent>
        </Card>

        {"error" in latest ? (
          <LoadError title="Generierung nicht geladen" message={latest.error} />
        ) : latest.job ? (
          <JobPanel job={latest.job} units={scope.stations} />
        ) : (
          <Card aria-label="Letzte Generierung" className="border-dashed shadow-none">
            <CardHeader>
              <CardTitle>Letzte Generierung</CardTitle>
              <CardDescription>
                Kein Ergebnis verfügbar. Generierungen werden nur bis zum Neustart des Backends vorgehalten.
              </CardDescription>
            </CardHeader>
          </Card>
        )}
      </div>
    </div>
  );
}
