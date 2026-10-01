import {IAvailabilityRepository} from '@/application/ports/availability.repository';
import {AvailabilityEmployee} from '@/entities/models/availability.model';

export interface IGetAllAvailabilityUseCase {
    (input: { caseId: number; monthYear: string }): Promise<AvailabilityEmployee[]>;
}

export function makeGetAllAvailabilityUseCase(
    availabilityRepository: IAvailabilityRepository
): IGetAllAvailabilityUseCase {
    return async ({caseId, monthYear}) => {
        return availabilityRepository.getAll(caseId, monthYear);
    };
}
