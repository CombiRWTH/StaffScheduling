import { IScheduleRepository } from "@/application/ports/schedule.repository";

export interface ISelectScheduleUseCase {
  (input: { caseId: number; monthYear: string; scheduleId: string }): Promise<void>;
}

export function makeSelectScheduleUseCase(scheduleRepository: IScheduleRepository): ISelectScheduleUseCase {
  return async ({ caseId, monthYear, scheduleId }) => {
    return scheduleRepository.select(caseId, monthYear, scheduleId);
  };
}
