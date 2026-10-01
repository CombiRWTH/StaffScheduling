import { IAvailabilityRepository } from "@/application/ports/availability.repository";
import { IGlobalAvailabilityRepository } from "@/application/ports/global-availability.repository";
import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface ICreateGlobalAvailabilityUseCase {
  (input: { caseId: number; monthYear: string; entry: AvailabilityEmployee }): Promise<void>;
}

export function makeCreateGlobalAvailabilityUseCase(
  globalAvailabilityRepository: IGlobalAvailabilityRepository,
  availabilityRepository: IAvailabilityRepository,
): ICreateGlobalAvailabilityUseCase {
  return async ({ caseId, monthYear, entry }) => {
    await availabilityRepository.delete(caseId, monthYear, entry.key);
    await globalAvailabilityRepository.create(caseId, monthYear, entry);
    await availabilityRepository.generateFromGlobal(caseId, monthYear, entry);
  };
}
