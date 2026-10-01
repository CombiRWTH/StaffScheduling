import {IAvailabilityRepository} from '@/application/ports/availability.repository';
import {IGlobalAvailabilityRepository} from '@/application/ports/global-availability.repository';

export interface IDeleteGlobalAvailabilityUseCase {
    (input: { caseId: number; monthYear: string; key: number }): Promise<void>;
}

export function makeDeleteGlobalAvailabilityUseCase(
    globalAvailabilityRepository: IGlobalAvailabilityRepository,
    availabilityRepository: IAvailabilityRepository
): IDeleteGlobalAvailabilityUseCase {
    return async ({caseId, monthYear, key}) => {
        await availabilityRepository.delete(caseId, monthYear, key);
        await globalAvailabilityRepository.delete(caseId, monthYear, key);
    };
}
