import { ScheduleSolutionRaw } from "@/entities/models/schedule.model";
import { ScheduleNotFoundError } from "@/entities/errors/schedule.errors";
import { IScheduleRepository } from "@/application/ports/schedule.repository";

export interface IGetScheduleUseCase {
  (input: { caseId: number; monthYear: string; scheduleId: string }): Promise<ScheduleSolutionRaw>;
}

export function makeGetScheduleUseCase(scheduleRepository: IScheduleRepository): IGetScheduleUseCase {
  return async ({ caseId, monthYear, scheduleId }) => {
    const schedule = await scheduleRepository.getSchedule(caseId, monthYear, scheduleId);
    if (!schedule) throw new ScheduleNotFoundError(scheduleId);
    return schedule;
  };
}
