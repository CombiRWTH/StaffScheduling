import type { IUpdateAvailabilityUseCase } from "@/application/use-cases/availability/update-availability.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IUpdateAvailabilityController {
  (input: {
    caseId: number;
    monthYear: string;
    key: number;
    data: Partial<AvailabilityEmployee>;
  }): Promise<{ data: void } | { error: string }>;
}

export function makeUpdateAvailabilityController(
  updateAvailabilityUseCase: IUpdateAvailabilityUseCase,
): IUpdateAvailabilityController {
  return async ({ caseId, monthYear, key, data }) => {
    try {
      validateMonthYear(monthYear);
      await updateAvailabilityUseCase({ caseId, monthYear, key, data });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
