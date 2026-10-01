import { randomUUID } from "crypto";
import type { ISolverService } from "@/application/ports/solver.service";
import type { IJobRepository } from "@/application/ports/job.repository";
import type { IScheduleRepository } from "@/application/ports/schedule.repository";
import type { DeleteParams, SolverJob } from "@/entities/models/solver.model";
import type { ScheduleSolutionRaw } from "@/entities/models";

export interface IExecuteSolverDeleteUseCase {
  (input: { caseId: number; monthYear: string; params: DeleteParams; solution?: ScheduleSolutionRaw }): Promise<{
    job: SolverJob;
  }>;
}

export function makeExecuteSolverDeleteUseCase(
  solverService: ISolverService,
  jobRepository: IJobRepository,
  scheduleRepository: IScheduleRepository,
): IExecuteSolverDeleteUseCase {
  return async ({ caseId, monthYear, params, solution }) => {
    const startTime = Date.now();
    const result = await solverService.deleteData(params, solution);

    const job: SolverJob = {
      id: randomUUID(),
      type: "delete",
      status: result.success ? "completed" : "failed",
      caseId,
      params,
      error: result.error,
      consoleOutput: result.consoleOutput,
      createdAt: new Date(startTime).toISOString(),
      completedAt: new Date().toISOString(),
      duration: result.duration,
    };

    await jobRepository.create(caseId, monthYear, job);

    if (!result.success) {
      throw new Error(`Delete failed: ${result.error}`);
    }

    // Remove the last-inserted marker now that the data has been deleted
    await scheduleRepository.clearLastInserted(caseId, monthYear);

    return { job };
  };
}
