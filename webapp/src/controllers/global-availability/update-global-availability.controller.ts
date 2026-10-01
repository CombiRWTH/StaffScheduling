import type { IUpdateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/update-global-availability.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IUpdateGlobalAvailabilityController {
  (input: {
    caseId: number;
    monthYear: string;
    key: number;
    data: Partial<AvailabilityEmployee>;
  }): Promise<{ data: void } | { error: string }>;
}

export function makeUpdateGlobalAvailabilityController(
  updateGlobalAvailabilityUseCase: IUpdateGlobalAvailabilityUseCase,
): IUpdateGlobalAvailabilityController {
  return async ({ caseId, monthYear, key, data }) => {
    try {
      validateMonthYear(monthYear);
      await updateGlobalAvailabilityUseCase({ caseId, monthYear, key, data });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
