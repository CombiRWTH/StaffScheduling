import type { IGetGlobalAvailabilityByKeyUseCase } from "@/application/use-cases/global-availability/get-global-availability-by-key.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetGlobalAvailabilityByKeyController {
  (input: {
    caseId: number;
    monthYear: string;
    key: number;
  }): Promise<{ data: AvailabilityEmployee } | { error: string }>;
}

export function makeGetGlobalAvailabilityByKeyController(
  getGlobalAvailabilityByKeyUseCase: IGetGlobalAvailabilityByKeyUseCase,
): IGetGlobalAvailabilityByKeyController {
  return async ({ caseId, monthYear, key }) => {
    try {
      validateMonthYear(monthYear);
      const availability = await getGlobalAvailabilityByKeyUseCase({ caseId, monthYear, key });
      return { data: availability };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
