import {IGlobalAvailabilityRepository} from '@/application/ports/global-availability.repository';
import {ResourceNotFoundError} from '@/entities/errors/base.errors';
import {AvailabilityEmployee} from '@/entities/models/availability.model';

export interface IGetGlobalAvailabilityByKeyUseCase {
    (input: { caseId: number; monthYear: string; key: number }): Promise<AvailabilityEmployee>;
}

export function makeGetGlobalAvailabilityByKeyUseCase(
    globalAvailabilityRepository: IGlobalAvailabilityRepository
): IGetGlobalAvailabilityByKeyUseCase {
    return async ({caseId, monthYear, key}) => {
        const entry = await globalAvailabilityRepository.getByKey(caseId, monthYear, key);
        if (!entry) throw new ResourceNotFoundError(`Global availability entry with key ${key} not found`);
        return entry;
    };
}
