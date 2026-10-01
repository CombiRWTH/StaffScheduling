import type {ISelectScheduleUseCase} from '@/application/use-cases/schedule/select-schedule.use-case';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear, validateScheduleId} from '@/entities/validation/input-validators';

export interface ISelectScheduleController {
    (input: { caseId: number; monthYear: string; scheduleId: string }): Promise<
        { data: void } | { error: string }
    >;
}

export function makeSelectScheduleController(
    selectScheduleUseCase: ISelectScheduleUseCase
): ISelectScheduleController {
    return async ({caseId, monthYear, scheduleId}) => {
        try {
            validateMonthYear(monthYear);
            validateScheduleId(scheduleId);
            await selectScheduleUseCase({caseId, monthYear, scheduleId});
            return {data: undefined};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
