import type { IGetAllJobsUseCase } from "@/application/use-cases/jobs/get-all-jobs.use-case";
import type { SolverJob } from "@/entities/models/solver.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetAllJobsController {
  (input: { caseId: number; monthYear: string }): Promise<{ data: SolverJob[] } | { error: string }>;
}

export function makeGetAllJobsController(getAllJobsUseCase: IGetAllJobsUseCase): IGetAllJobsController {
  return async ({ caseId, monthYear }) => {
    try {
      validateMonthYear(monthYear);
      const jobs = await getAllJobsUseCase({ caseId, monthYear });
      return { data: jobs };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
