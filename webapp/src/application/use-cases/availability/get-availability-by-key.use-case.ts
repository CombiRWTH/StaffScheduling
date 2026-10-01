import { IAvailabilityRepository } from "@/application/ports/availability.repository";
import { ResourceNotFoundError } from "@/entities/errors/base.errors";
import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface IGetAvailabilityByKeyUseCase {
  (input: { caseId: number; monthYear: string; key: number }): Promise<AvailabilityEmployee>;
}

export function makeGetAvailabilityByKeyUseCase(
  availabilityRepository: IAvailabilityRepository,
): IGetAvailabilityByKeyUseCase {
  return async ({ caseId, monthYear, key }) => {
    const entry = await availabilityRepository.getByKey(caseId, monthYear, key);
    if (!entry) throw new ResourceNotFoundError(`Availability entry with key ${key} not found`);
    return entry;
  };
}
