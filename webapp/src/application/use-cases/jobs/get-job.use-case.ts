import { SolverJob } from "@/entities/models/solver.model";
import { ResourceNotFoundError } from "@/entities/errors/base.errors";
import { IJobRepository } from "@/application/ports/job.repository";

export interface IGetJobUseCase {
  (input: { caseId: number; monthYear: string; jobId: string }): Promise<SolverJob>;
}

export function makeGetJobUseCase(jobRepository: IJobRepository): IGetJobUseCase {
  return async ({ caseId, monthYear, jobId }) => {
    const job = await jobRepository.getById(caseId, monthYear, jobId);
    if (!job) throw new ResourceNotFoundError(`Job with id "${jobId}" not found`);
    return job;
  };
}
