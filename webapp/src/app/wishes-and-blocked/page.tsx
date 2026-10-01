import { WishesAndBlockedPageClient } from "./wishes-and-blocked-page-client";
import { getAllWishesAction } from "@/features/wishes_and_blocked/wishes-and-blocked.actions";
import { listAvailableCaseIdsForMonthAction } from "@/features/cases/cases.actions";
import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";

interface WishesCaseData {
  caseId: number;
  employees: WishesAndBlockedEmployee[];
}

interface WishesCaseError {
  caseId: number;
  error: string;
}

type WishesResult =
  | { caseId: number; employees: WishesAndBlockedEmployee[]; error: null }
  | { caseId: number; employees: WishesAndBlockedEmployee[]; error: string };

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default async function WishesAndBlockedPage({
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

  const wishesResults: WishesResult[] = await Promise.all(
    selectedCaseIds.map(async (caseId) => {
      try {
        return {
          caseId,
          employees: await getAllWishesAction(caseId, monthYear),
          error: null,
        };
      } catch (error) {
        return {
          caseId,
          employees: [],
          error: getErrorMessage(error),
        };
      }
    }),
  );

  const wishesCases: WishesCaseData[] = wishesResults
    .filter((result) => result.error === null)
    .map(({ caseId, employees }) => ({ caseId, employees }));

  const wishesErrors: WishesCaseError[] = wishesResults
    .filter(
      (result): result is { caseId: number; employees: WishesAndBlockedEmployee[]; error: string } =>
        result.error !== null,
    )
    .map(({ caseId, error }) => ({ caseId, error }));

  return (
    <WishesAndBlockedPageClient
      monthYear={monthYear}
      wishesCases={wishesCases}
      wishesErrors={wishesErrors}
      availableCaseIds={availableCaseIds}
    />
  );
}
