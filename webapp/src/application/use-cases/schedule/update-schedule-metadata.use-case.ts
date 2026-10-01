import {IScheduleRepository} from '@/application/ports/schedule.repository';

export interface IUpdateScheduleMetadataUseCase {
    (input: {
        caseId: number;
        monthYear: string;
        scheduleId: string;
        updates: { description?: string; comment?: string }
    }): Promise<void>;
}

export function makeUpdateScheduleMetadataUseCase(
    scheduleRepository: IScheduleRepository
): IUpdateScheduleMetadataUseCase {
    return async ({caseId, monthYear, scheduleId, updates}) => {
        return scheduleRepository.updateMetadata(caseId, monthYear, scheduleId, updates);
    };
}
