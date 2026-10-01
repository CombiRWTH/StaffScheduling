import {IAvailabilityRepository} from '@/application/ports/availability.repository';
import {AvailabilityEmployee} from '@/entities/models/availability.model';

export interface IUpdateAvailabilityUseCase {
    (input: { caseId: number; monthYear: string; key: number; data: Partial<AvailabilityEmployee> }): Promise<void>;
}

export function makeUpdateAvailabilityUseCase(
    availabilityRepository: IAvailabilityRepository
): IUpdateAvailabilityUseCase {
    return async ({caseId, monthYear, key, data}) => {
        return availabilityRepository.update(caseId, monthYear, key, data);
    };
}
