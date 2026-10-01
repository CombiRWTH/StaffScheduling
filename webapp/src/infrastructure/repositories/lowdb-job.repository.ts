import { IJobRepository } from "@/application/ports/job.repository";
import { SolverJob } from "@/entities/models/solver.model";
import { getJobHistoryDb } from "@/infrastructure/persistence/lowdb/jobs.db";

const DEFAULT_MAX_JOBS = 10;

export class LowdbJobRepository implements IJobRepository {
  async getAll(caseId: number, monthYear: string): Promise<SolverJob[]> {
    const db = await getJobHistoryDb(caseId, monthYear);
    await db.read();
    return db.data.jobs;
  }

  async getById(caseId: number, monthYear: string, jobId: string): Promise<SolverJob | null> {
    const db = await getJobHistoryDb(caseId, monthYear);
    await db.read();
    return db.data.jobs.find((j) => j.id === jobId) ?? null;
  }

  async create(caseId: number, monthYear: string, job: SolverJob): Promise<void> {
    const db = await getJobHistoryDb(caseId, monthYear);
    await db.read();
    db.data.jobs.unshift(job);

    if (db.data.jobs.length > DEFAULT_MAX_JOBS) {
      db.data.jobs = db.data.jobs.slice(0, DEFAULT_MAX_JOBS);
    }

    await db.write();
  }

  async cleanup(caseId: number, monthYear: string, maxJobs?: number): Promise<void> {
    const limit = maxJobs ?? DEFAULT_MAX_JOBS;
    const db = await getJobHistoryDb(caseId, monthYear);
    await db.read();

    if (db.data.jobs.length > limit) {
      db.data.jobs = db.data.jobs.slice(0, limit);
      await db.write();
    }
  }
}
