import { IGlobalAvailabilityRepository } from "@/application/ports/global-availability.repository";
import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface IGetAllGlobalAvailabilityUseCase {
  (input: { caseId: number; monthYear: string }): Promise<AvailabilityEmployee[]>;
}

export function makeGetAllGlobalAvailabilityUseCase(
  globalAvailabilityRepository: IGlobalAvailabilityRepository,
): IGetAllGlobalAvailabilityUseCase {
  return async ({ caseId, monthYear }) => {
    return globalAvailabilityRepository.getAll(caseId, monthYear);
  };
}
