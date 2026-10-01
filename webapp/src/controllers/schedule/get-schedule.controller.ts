import type { IGetScheduleUseCase } from "@/application/use-cases/schedule/get-schedule.use-case";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear, validateScheduleId } from "@/entities/validation/input-validators";

export interface IGetScheduleController {
  (input: {
    caseId: number;
    monthYear: string;
    scheduleId: string;
  }): Promise<{ data: ScheduleSolutionRaw } | { error: string }>;
}

export function makeGetScheduleController(getScheduleUseCase: IGetScheduleUseCase): IGetScheduleController {
  return async ({ caseId, monthYear, scheduleId }) => {
    try {
      validateMonthYear(monthYear);
      validateScheduleId(scheduleId);
      const schedule = await getScheduleUseCase({ caseId, monthYear, scheduleId });
      return { data: schedule };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
