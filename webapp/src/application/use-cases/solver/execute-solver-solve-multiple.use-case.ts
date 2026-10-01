import { randomUUID } from "crypto";
import type { ISolverService } from "@/application/ports/solver.service";
import type { IJobRepository } from "@/application/ports/job.repository";
import type { SolveMultipleParams, SolveMultipleScheduleInfo, SolverJob } from "@/entities/models/solver.model";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";
import { SolveUnknownError } from "@/entities/errors/solver.errors";

export type { SolveMultipleScheduleInfo };

export interface IExecuteSolverSolveMultipleUseCase {
  (input: {
    caseId: number;
    monthYear: string;
    params: SolveMultipleParams;
  }): Promise<{ job: SolverJob; scheduleInfo: SolveMultipleScheduleInfo; solutions: ScheduleSolutionRaw[] }>;
}

export function makeExecuteSolverSolveMultipleUseCase(
  solverService: ISolverService,
  jobRepository: IJobRepository,
): IExecuteSolverSolveMultipleUseCase {
  return async ({ caseId, monthYear, params }) => {
    const startTime = Date.now();
    const result = await solverService.solveMultiple(params);

    // Keep the legacy scheduleInfo shape for existing consumers.
    const scheduleInfo: SolveMultipleScheduleInfo = {
      solutionsGenerated: result.feasibleCount,
      scheduleFiles: [], // CLI-only field; the API returns solutions directly.
      feasibleSolutions: result.feasibleWeightIds,
    };

    const job: SolverJob = {
      id: randomUUID(),
      type: "solve-multiple",
      status: result.success ? "completed" : "failed",
      caseId,
      params,
      error: result.error,
      consoleOutput: result.consoleOutput,
      createdAt: new Date(startTime).toISOString(),
      completedAt: new Date().toISOString(),
      duration: result.duration,
      metadata: {
        solutionsGenerated: result.feasibleCount,
        expectedSolutions: 3,
        feasibleSolutions: result.feasibleWeightIds,
      },
    };

    await jobRepository.create(caseId, monthYear, job);

    if (!result.success) {
      throw new SolveUnknownError();
    }

    return { job, scheduleInfo, solutions: result.solutions };
  };
}
