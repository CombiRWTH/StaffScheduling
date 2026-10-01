import type { ScheduleSolution, ScheduleSolutionRaw } from "@/entities/models/schedule.model";

export interface IScheduleParserService {
  /**
   * Parses a raw schedule solution (from solver JSON files) into a rich
   * ScheduleSolution with computed wish-fulfilment data and statistics.
   */
  parseSolution(jsonData: ScheduleSolutionRaw): ScheduleSolution;
}
