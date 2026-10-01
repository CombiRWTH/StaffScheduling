import type {IUpdateMinimalStaffUseCase} from '@/application/use-cases/minimal-staff/update-minimal-staff.use-case';
import type {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IUpdateMinimalStaffController {
    (input: { caseId: number; monthYear: string; data: MinimalStaffRequirements }): Promise<
        { data: void } | { error: string }
    >;
}

export function makeUpdateMinimalStaffController(
    updateMinimalStaffUseCase: IUpdateMinimalStaffUseCase
): IUpdateMinimalStaffController {
    return async ({caseId, monthYear, data}) => {
        try {
            validateMonthYear(monthYear);
            await updateMinimalStaffUseCase({caseId, monthYear, data});
            return {data: undefined};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
