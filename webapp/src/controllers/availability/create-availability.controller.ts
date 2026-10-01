import type {ICreateAvailabilityUseCase} from '@/application/use-cases/availability/create-availability.use-case';
import {isDomainError} from '@/entities/errors/base.errors';
import type {AvailabilityEmployee} from '@/entities/models/availability.model';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface ICreateAvailabilityController {
    (input: { caseId: number; monthYear: string; entry: AvailabilityEmployee }): Promise<
        { data: void } | { error: string }
    >;
}

export function makeCreateAvailabilityController(
    createAvailabilityUseCase: ICreateAvailabilityUseCase
): ICreateAvailabilityController {
    return async ({caseId, monthYear, entry}) => {
        try {
            validateMonthYear(monthYear);
            await createAvailabilityUseCase({caseId, monthYear, entry});
            return {data: undefined};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
