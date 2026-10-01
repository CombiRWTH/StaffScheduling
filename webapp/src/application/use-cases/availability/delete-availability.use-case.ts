import { IAvailabilityRepository } from "@/application/ports/availability.repository";

export interface IDeleteAvailabilityUseCase {
  (input: { caseId: number; monthYear: string; key: number }): Promise<void>;
}

export function makeDeleteAvailabilityUseCase(
  availabilityRepository: IAvailabilityRepository,
): IDeleteAvailabilityUseCase {
  return async ({ caseId, monthYear, key }) => {
    return availabilityRepository.delete(caseId, monthYear, key);
  };
}
