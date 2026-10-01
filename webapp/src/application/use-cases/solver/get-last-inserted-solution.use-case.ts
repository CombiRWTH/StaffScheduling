import type { IScheduleRepository } from "@/application/ports/schedule.repository";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";

export interface IGetLastInsertedSolutionUseCase {
  (input: { caseId: number; monthYear: string }): Promise<ScheduleSolutionRaw | null>;
}

export function makeGetLastInsertedSolutionUseCase(
  scheduleRepository: IScheduleRepository,
): IGetLastInsertedSolutionUseCase {
  return async ({ caseId, monthYear }) => {
    return scheduleRepository.getLastInserted(caseId, monthYear);
  };
}
