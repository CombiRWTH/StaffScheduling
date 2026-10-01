import { IAvailabilityRepository } from "@/application/ports/availability.repository";
import { IGlobalAvailabilityRepository } from "@/application/ports/global-availability.repository";
import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface IUpdateGlobalAvailabilityUseCase {
  (input: { caseId: number; monthYear: string; key: number; data: Partial<AvailabilityEmployee> }): Promise<void>;
}

export function makeUpdateGlobalAvailabilityUseCase(
  globalAvailabilityRepository: IGlobalAvailabilityRepository,
  availabilityRepository: IAvailabilityRepository,
): IUpdateGlobalAvailabilityUseCase {
  return async ({ caseId, monthYear, key, data }) => {
    await availabilityRepository.delete(caseId, monthYear, key);
    await globalAvailabilityRepository.update(caseId, monthYear, key, data);
    const updated = await globalAvailabilityRepository.getByKey(caseId, monthYear, key);
    if (updated) {
      await availabilityRepository.generateFromGlobal(caseId, monthYear, updated);
    }
  };
}
