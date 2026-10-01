import type { SolverJob } from "@/entities/models/solver.model";

interface StoredSolveJobHistory {
  planningUnitIds: number[];
  jobs: SolverJob[];
}

export function getSolveJobHistoryKey(monthYear: string, planningUnitIds: number[]): string {
  return `solve-jobs:${monthYear}:${[...planningUnitIds].sort((a, b) => a - b).join(",")}`;
}

export function readSolveJobHistory(storageKey: string): SolverJob[] {
  const storedJobs = localStorage.getItem(storageKey);
  if (!storedJobs) return [];

  const parsed = JSON.parse(storedJobs) as StoredSolveJobHistory | SolverJob[];
  return Array.isArray(parsed) ? parsed.slice(0, 10) : parsed.jobs.slice(0, 10);
}

export function writeSolveJobHistory(storageKey: string, planningUnitIds: number[], jobs: SolverJob[]): SolverJob[] {
  const lastJobs = jobs.slice(0, 10);
  const data: StoredSolveJobHistory = {
    planningUnitIds: [...planningUnitIds].sort((a, b) => a - b),
    jobs: lastJobs,
  };

  localStorage.setItem(storageKey, JSON.stringify(data));
  return lastJobs;
}
