import type {ISaveScheduleUseCase} from '@/application/use-cases/schedule/save-schedule.use-case';
import type {ScheduleMetadata, ScheduleSolutionRaw} from '@/entities/models/schedule.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear, validateScheduleId} from '@/entities/validation/input-validators';

export interface ISaveScheduleController {
    (input: {
        caseId: number;
        monthYear: string;
        scheduleId: string;
        solution: ScheduleSolutionRaw;
        description?: string;
    }): Promise<{ data: ScheduleMetadata } | { error: string }>;
}

export function makeSaveScheduleController(
    saveScheduleUseCase: ISaveScheduleUseCase
): ISaveScheduleController {
    return async ({caseId, monthYear, scheduleId, solution, description}) => {
        try {
            validateMonthYear(monthYear);
            validateScheduleId(scheduleId);
            const metadata = await saveScheduleUseCase({caseId, monthYear, scheduleId, solution, description});
            return {data: metadata};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
