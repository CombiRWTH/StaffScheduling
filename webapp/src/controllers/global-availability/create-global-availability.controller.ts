import type { ICreateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/create-global-availability.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface ICreateGlobalAvailabilityController {
  (input: {
    caseId: number;
    monthYear: string;
    entry: AvailabilityEmployee;
  }): Promise<{ data: void } | { error: string }>;
}

export function makeCreateGlobalAvailabilityController(
  createGlobalAvailabilityUseCase: ICreateGlobalAvailabilityUseCase,
): ICreateGlobalAvailabilityController {
  return async ({ caseId, monthYear, entry }) => {
    try {
      validateMonthYear(monthYear);
      await createGlobalAvailabilityUseCase({ caseId, monthYear, entry });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
