import { getSolverApiConfig } from "@/lib/config/app-config";
import type { SolveParams, SolverJob } from "@/entities/models/solver.model";

interface SolveJobStartResponse {
  job_id: string;
  status: SolverJob["status"];
}

interface BackendSolveJobResponse {
  job_id: string;
  status: SolverJob["status"];
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  result?: unknown;
  error?: string | null;
}

function getYearMonth(params: SolveParams): { year: number; month: number } {
  const [year, month] = params.start.split("-").map(Number);
  return { year, month };
}

function getPlanningUnitIds(params: SolveParams): number[] {
  return Array.isArray(params.unit) ? params.unit : [params.unit];
}

function getDuration(startedAt?: string | null, finishedAt?: string | null): number | undefined {
  if (!startedAt || !finishedAt) return undefined;
  return new Date(finishedAt).getTime() - new Date(startedAt).getTime();
}

function mapBackendJobToSolverJob(
  caseId: number,
  params: SolveParams,
  backendJob: SolveJobStartResponse | BackendSolveJobResponse,
): SolverJob {
  const startedAt = "started_at" in backendJob ? backendJob.started_at : null;
  const finishedAt = "finished_at" in backendJob ? backendJob.finished_at : null;

  return {
    id: backendJob.job_id,
    backendJobId: backendJob.job_id,
    type: "solve",
    status: backendJob.status,
    caseId,
    params,
    createdAt: "created_at" in backendJob ? backendJob.created_at : new Date().toISOString(),
    completedAt: finishedAt ?? undefined,
    duration: getDuration(startedAt, finishedAt),
    error: "error" in backendJob ? (backendJob.error ?? undefined) : undefined,
    result: "result" in backendJob ? backendJob.result : undefined,
  };
}

async function readError(response: Response): Promise<string> {
  return response.text();
}

export async function startBackendSolveJob(caseId: number, params: SolveParams): Promise<{ job: SolverJob }> {
  const { baseUrl } = getSolverApiConfig();
  const { year, month } = getYearMonth(params);

  const response = await fetch(`${baseUrl}/solve/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      planning_unit_ids: getPlanningUnitIds(params),
      year,
      month,
      timeout: params.timeout,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const backendJob = (await response.json()) as SolveJobStartResponse;
  return { job: mapBackendJobToSolverJob(caseId, params, backendJob) };
}

export async function getBackendSolveJob(
  caseId: number,
  params: SolveParams,
  jobId: string,
): Promise<{ job: SolverJob }> {
  const { baseUrl } = getSolverApiConfig();
  const response = await fetch(`${baseUrl}/solve/jobs/${jobId}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const backendJob = (await response.json()) as BackendSolveJobResponse;
  return { job: mapBackendJobToSolverJob(caseId, params, backendJob) };
}
