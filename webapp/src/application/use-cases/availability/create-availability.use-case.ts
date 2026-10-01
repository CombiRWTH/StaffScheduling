import { IAvailabilityRepository } from "@/application/ports/availability.repository";
import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface ICreateAvailabilityUseCase {
  (input: { caseId: number; monthYear: string; entry: AvailabilityEmployee }): Promise<void>;
}

export function makeCreateAvailabilityUseCase(
  availabilityRepository: IAvailabilityRepository,
): ICreateAvailabilityUseCase {
  return async ({ caseId, monthYear, entry }) => {
    return availabilityRepository.create(caseId, monthYear, entry);
  };
}
