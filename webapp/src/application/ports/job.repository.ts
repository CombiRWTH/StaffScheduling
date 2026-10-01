import { SolverJob } from "@/entities/models/solver.model";

export interface IJobRepository {
  getAll(caseId: number, monthYear: string): Promise<SolverJob[]>;

  getById(caseId: number, monthYear: string, jobId: string): Promise<SolverJob | null>;

  create(caseId: number, monthYear: string, job: SolverJob): Promise<void>;

  cleanup(caseId: number, monthYear: string, maxJobs?: number): Promise<void>;
}
