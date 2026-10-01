import { GlobalAvailabilityPageClient } from "./global-availability-page-client";
import { getAllGlobalAvailabilityAction } from "@/features/availability/availability.actions";
import { listAvailabilityTemplatesAction } from "@/features/templates/availability-templates.actions";
import { listAvailableCaseIdsForMonthAction } from "@/features/cases/cases.actions";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import type { TemplateSummary } from "@/entities/models/template.model";

interface GlobalAvailabilityCaseData {
  caseId: number;
  employees: AvailabilityEmployee[];
  templates: TemplateSummary[];
}

interface GlobalAvailabilityCaseError {
  caseId: number;
  error: string;
}

type GlobalAvailabilityResult =
  | { caseId: number; employees: AvailabilityEmployee[]; templates: TemplateSummary[]; error: null }
  | { caseId: number; employees: AvailabilityEmployee[]; templates: TemplateSummary[]; error: string };

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default async function GlobalAvailabilityPage({
  searchParams,
}: {
  searchParams: Promise<{ caseId?: string; caseIds?: string; monthYear?: string }>;
}) {
  const { caseId: caseIdStr, caseIds: caseIdsStr, monthYear } = await searchParams;
  const rawCaseIds = caseIdsStr ?? caseIdStr ?? "";
  const caseIds = Array.from(
    new Set(
      rawCaseIds
        .split(",")
        .map((id) => Number(id))
        .filter((id) => Number.isInteger(id) && id > 0),
    ),
  );

  if (!monthYear || !/^(0?[1-9]|1[0-2])_\d{4}$/.test(monthYear)) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Monat aus</div>
    );
  }

  const availableCaseIds = await listAvailableCaseIdsForMonthAction(monthYear);

  const selectedCaseIds = caseIds.filter((id) => availableCaseIds.includes(id));

  const results: GlobalAvailabilityResult[] = await Promise.all(
    selectedCaseIds.map(async (caseId) => {
      try {
        const [employees, templates] = await Promise.all([
          getAllGlobalAvailabilityAction(caseId, monthYear),
          listAvailabilityTemplatesAction(caseId),
        ]);
        return {
          caseId,
          employees,
          templates,
          error: null,
        };
      } catch (error) {
        return {
          caseId,
          employees: [],
          templates: [],
          error: getErrorMessage(error),
        };
      }
    }),
  );

  const globalAvailabilityCases: GlobalAvailabilityCaseData[] = results
    .filter((result) => result.error === null)
    .map(({ caseId, employees, templates }) => ({ caseId, employees, templates }));

  const globalAvailabilityErrors: GlobalAvailabilityCaseError[] = results
    .filter(
      (
        result,
      ): result is { caseId: number; employees: AvailabilityEmployee[]; templates: TemplateSummary[]; error: string } =>
        result.error !== null,
    )
    .map(({ caseId, error }) => ({ caseId, error }));

  return (
    <GlobalAvailabilityPageClient
      monthYear={monthYear}
      globalAvailabilityCases={globalAvailabilityCases}
      globalAvailabilityErrors={globalAvailabilityErrors}
      availableCaseIds={availableCaseIds}
    />
  );
}
