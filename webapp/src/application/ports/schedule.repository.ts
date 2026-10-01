import { ScheduleMetadata, SchedulesMetadata, ScheduleSolutionRaw } from "@/entities/models/schedule.model";

export interface IScheduleRepository {
  getMetadata(caseId: number, monthYear: string): Promise<SchedulesMetadata>;

  getSchedule(caseId: number, monthYear: string, scheduleId: string): Promise<ScheduleSolutionRaw | null>;

  save(
    caseId: number,
    monthYear: string,
    scheduleId: string,
    solution: ScheduleSolutionRaw,
    description?: string,
  ): Promise<ScheduleMetadata>;

  delete(caseId: number, monthYear: string, scheduleId: string): Promise<void>;

  select(caseId: number, monthYear: string, scheduleId: string): Promise<void>;

  getSelectedSchedule(caseId: number, monthYear: string): Promise<ScheduleSolutionRaw | null>;

  updateMetadata(
    caseId: number,
    monthYear: string,
    scheduleId: string,
    updates: {
      description?: string;
      comment?: string;
    },
  ): Promise<void>;

  /** Persists the solution that was last successfully inserted into TimeOffice.  */
  saveLastInserted(caseId: number, monthYear: string, solution: ScheduleSolutionRaw): Promise<void>;

  /** Returns the solution last inserted into TimeOffice, or null when none exists. */
  getLastInserted(caseId: number, monthYear: string): Promise<ScheduleSolutionRaw | null>;

  /** Removes the last-inserted marker (call after a successful delete). */
  clearLastInserted(caseId: number, monthYear: string): Promise<void>;
}
