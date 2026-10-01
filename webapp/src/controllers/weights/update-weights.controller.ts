import type { IUpdateWeightsUseCase } from "@/application/use-cases/weights/update-weights.use-case";
import type { Weights } from "@/entities/models/weights.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IUpdateWeightsController {
  (input: { caseId: number; monthYear: string; weights: Weights }): Promise<{ data: void } | { error: string }>;
}

export function makeUpdateWeightsController(updateWeightsUseCase: IUpdateWeightsUseCase): IUpdateWeightsController {
  return async ({ caseId, monthYear, weights }) => {
    try {
      validateMonthYear(monthYear);
      await updateWeightsUseCase({ caseId, monthYear, weights });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
