import { GlobalWishesAndBlockedPageClient } from "./global-wishes-and-blocked-page-client";
import { getAllGlobalWishesAction } from "@/features/global_wishes_and_blocked/global-wishes-and-blocked.actions";
import { getAllEmployeesAction } from "@/features/employees/employees.actions";
import { listGlobalWishesTemplatesAction } from "@/features/templates/global-wishes-templates.actions";
import { listAvailableCaseIdsForMonthAction } from "@/features/cases/cases.actions";
import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { Employee } from "@/entities/models/employee.model";
import { TemplateSummary } from "@/entities/models/template.model";

interface GlobalWishesCaseData {
  caseId: number;
  employees: WishesAndBlockedEmployee[];
  currentEmployees: Employee[];
  templates: TemplateSummary[];
}

interface GlobalWishesCaseError {
  caseId: number;
  error: string;
}

type GlobalWishesResult =
  | (GlobalWishesCaseData & { error: null })
  | { caseId: number; employees: []; currentEmployees: []; templates: []; error: string };

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default async function GlobalWishesAndBlockedPage({
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

  if (!monthYear) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Monat aus</div>
    );
  }

  if (!/^(0?[1-9]|1[0-2])_\d{4}$/.test(monthYear)) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Monat aus</div>
    );
  }

  const availableCaseIds = await listAvailableCaseIdsForMonthAction(monthYear);

  const selectedCaseIds = caseIds.filter((id) => availableCaseIds.includes(id));

  const globalWishesResults: GlobalWishesResult[] = await Promise.all(
    selectedCaseIds.map(async (caseId) => {
      try {
        const [employees, currentEmployees, templates] = await Promise.all([
          getAllGlobalWishesAction(caseId, monthYear),
          getAllEmployeesAction(caseId, monthYear),
          listGlobalWishesTemplatesAction(caseId),
        ]);

        return { caseId, employees, currentEmployees, templates, error: null };
      } catch (error) {
        return {
          caseId,
          employees: [],
          currentEmployees: [],
          templates: [],
          error: getErrorMessage(error),
        };
      }
    }),
  );

  const globalWishesCases: GlobalWishesCaseData[] = globalWishesResults
    .filter((result): result is GlobalWishesCaseData & { error: null } => result.error === null)
    .map(({ caseId, employees, currentEmployees, templates }) => ({ caseId, employees, currentEmployees, templates }));

  const globalWishesErrors: GlobalWishesCaseError[] = globalWishesResults
    .filter(
      (result): result is { caseId: number; employees: []; currentEmployees: []; templates: []; error: string } =>
        result.error !== null,
    )
    .map(({ caseId, error }) => ({ caseId, error }));

  return (
    <GlobalWishesAndBlockedPageClient
      monthYear={monthYear}
      globalWishesCases={globalWishesCases}
      globalWishesErrors={globalWishesErrors}
      availableCaseIds={availableCaseIds}
    />
  );
}
