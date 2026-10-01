import type {IGetAllGlobalAvailabilityUseCase} from '@/application/use-cases/global-availability/get-all-global-availability.use-case';
import {isDomainError} from '@/entities/errors/base.errors';
import type {AvailabilityEmployee} from '@/entities/models/availability.model';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IGetAllGlobalAvailabilityController {
    (input: { caseId: number; monthYear: string }): Promise<
        { data: AvailabilityEmployee[] } | { error: string }
    >;
}

export function makeGetAllGlobalAvailabilityController(
    getAllGlobalAvailabilityUseCase: IGetAllGlobalAvailabilityUseCase
): IGetAllGlobalAvailabilityController {
    return async ({caseId, monthYear}) => {
        try {
            validateMonthYear(monthYear);
            const availability = await getAllGlobalAvailabilityUseCase({caseId, monthYear});
            return {data: availability};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
