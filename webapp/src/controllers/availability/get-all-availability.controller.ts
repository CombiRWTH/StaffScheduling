import type { IGetAllAvailabilityUseCase } from "@/application/use-cases/availability/get-all-availability.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetAllAvailabilityController {
  (input: { caseId: number; monthYear: string }): Promise<{ data: AvailabilityEmployee[] } | { error: string }>;
}

export function makeGetAllAvailabilityController(
  getAllAvailabilityUseCase: IGetAllAvailabilityUseCase,
): IGetAllAvailabilityController {
  return async ({ caseId, monthYear }) => {
    try {
      validateMonthYear(monthYear);
      const availability = await getAllAvailabilityUseCase({ caseId, monthYear });
      return { data: availability };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
