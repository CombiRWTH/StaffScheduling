import {IScheduleRepository} from '@/application/ports/schedule.repository';

export interface IDeleteScheduleUseCase {
    (input: { caseId: number; monthYear: string; scheduleId: string }): Promise<void>;
}

export function makeDeleteScheduleUseCase(
    scheduleRepository: IScheduleRepository
): IDeleteScheduleUseCase {
    return async ({caseId, monthYear, scheduleId}) => {
        return scheduleRepository.delete(caseId, monthYear, scheduleId);
    };
}
