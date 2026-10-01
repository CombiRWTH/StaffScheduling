import { WeightsPageClient } from "./weights-page-client";
import { getWeightsAction } from "@/features/weights/weights.actions";
import { listAvailableCaseIdsForMonthAction } from "@/features/cases/cases.actions";
import { Weights } from "@/entities/models/weights.model";

interface WeightsCaseData {
  caseId: number;
  weights: Weights;
}

interface WeightsCaseError {
  caseId: number;
  error: string;
}

type WeightsResult =
  { caseId: number; weights: Weights | null; error: null } | { caseId: number; weights: null; error: string };

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default async function WeightsPage({
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

  const weightsResults: WeightsResult[] = await Promise.all(
    selectedCaseIds.map(async (caseId) => {
      try {
        return {
          caseId,
          weights: await getWeightsAction(caseId, monthYear),
          error: null,
        };
      } catch (error) {
        return {
          caseId,
          weights: null,
          error: getErrorMessage(error),
        };
      }
    }),
  );

  const weightsCases: WeightsCaseData[] = weightsResults
    .filter((result): result is { caseId: number; weights: Weights; error: null } => result.error === null)
    .map(({ caseId, weights }) => ({ caseId, weights }));

  const weightsErrors: WeightsCaseError[] = weightsResults
    .filter((result): result is { caseId: number; weights: null; error: string } => result.error !== null)
    .map(({ caseId, error }) => ({ caseId, error }));

  return (
    <WeightsPageClient
      monthYear={monthYear}
      weightsCases={weightsCases}
      weightsErrors={weightsErrors}
      availableCaseIds={availableCaseIds}
    />
  );
}
