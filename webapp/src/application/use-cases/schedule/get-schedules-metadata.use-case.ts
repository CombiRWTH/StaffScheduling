import { SchedulesMetadata } from "@/entities/models/schedule.model";
import { IScheduleRepository } from "@/application/ports/schedule.repository";

export interface IGetSchedulesMetadataUseCase {
  (input: { caseId: number; monthYear: string }): Promise<SchedulesMetadata>;
}

export function makeGetSchedulesMetadataUseCase(scheduleRepository: IScheduleRepository): IGetSchedulesMetadataUseCase {
  return async ({ caseId, monthYear }) => {
    return scheduleRepository.getMetadata(caseId, monthYear);
  };
}
