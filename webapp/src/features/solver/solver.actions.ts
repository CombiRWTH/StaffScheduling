'use server';

import { revalidatePath } from 'next/cache';
import { getInjection } from '@/di/container';
import { getBackendSolveJob, startBackendSolveJob } from '@/features/solver/solve-job-api';
import type {
    DeleteParams,
    FetchParams,
    ImportSolutionResult,
    InsertParams,
    SolveMultipleParams,
    SolveMultipleScheduleInfo,
    SolveParams,
    SolverJob,
} from '@/entities/models/solver.model';
import type { ActionResult } from '@/entities/models/action-result.model';
import type { SolverHealthResult, SolverProgress } from '@/application/ports/solver.service';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

export async function checkSolverHealth(): Promise<ActionResult<SolverHealthResult>> {
    const controller = getInjection('ICheckSolverHealthController');
    const result = await controller();
    if ('error' in result) return { success: false, error: result.error };
    return { success: true, data: result.data };
}

export async function solverFetch(
    caseId: number,
    monthYear: string,
    params: FetchParams
): Promise<ActionResult<{ job: SolverJob }>> {
    const controller = getInjection('IExecuteSolverFetchController');
    const result = await controller({ caseId, monthYear, params });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function solverSolve(
    caseId: number,
    monthYear: string,
    params: SolveParams
): Promise<ActionResult<{ job: SolverJob; solution: ScheduleSolutionRaw }>> {
    const controller = getInjection('IExecuteSolverSolveController');
    const result = await controller({ caseId, monthYear, params });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function startSolveJob(
    caseId: number,
    params: SolveParams
): Promise<ActionResult<{ job: SolverJob }>> {
    try {
        return { success: true, data: await startBackendSolveJob(caseId, params) };
    } catch (error) {
        return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
}

export async function checkSolveJob(
    caseId: number,
    params: SolveParams,
    jobId: string
): Promise<ActionResult<{ job: SolverJob }>> {
    try {
        return { success: true, data: await getBackendSolveJob(caseId, params, jobId) };
    } catch (error) {
        return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
}

export async function solverSolveMultiple(
    caseId: number,
    monthYear: string,
    params: SolveMultipleParams
): Promise<ActionResult<{ job: SolverJob; scheduleInfo: SolveMultipleScheduleInfo; solutions: ScheduleSolutionRaw[] }>> {
    const controller = getInjection('IExecuteSolverSolveMultipleController');
    const result = await controller({ caseId, monthYear, params });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function solverInsert(
    caseId: number,
    monthYear: string,
    params: InsertParams,
    solution?: ScheduleSolutionRaw
): Promise<ActionResult<{ job: SolverJob }>> {
    const controller = getInjection('IExecuteSolverInsertController');
    const result = await controller({ caseId, monthYear, params, solution });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function solverDelete(
    caseId: number,
    monthYear: string,
    params: DeleteParams,
    solution?: ScheduleSolutionRaw
): Promise<ActionResult<{ job: SolverJob }>> {
    const controller = getInjection('IExecuteSolverDeleteController');
    const result = await controller({ caseId, monthYear, params, solution });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function importSolution(
    caseId: number,
    monthYear: string,
    params: { start: string; end: string; solutionType: string; solution: ScheduleSolutionRaw }
): Promise<ActionResult<ImportSolutionResult>> {
    const controller = getInjection('IImportSolutionController');
    const result = await controller({ caseId, monthYear, ...params });
    if ('error' in result) return { success: false, error: result.error };
    revalidatePath('/schedule');
    revalidatePath('/solver');
    revalidatePath('/workflow');
    return { success: true, data: result.data };
}

export async function getJobs(
    caseId: number,
    monthYear: string
): Promise<{ jobs: SolverJob[] }> {
    const controller = getInjection('IGetAllJobsController');
    const result = await controller({ caseId, monthYear });
    if ('error' in result) throw new Error(result.error);
    return { jobs: result.data };
}

export async function getJob(
    caseId: number,
    monthYear: string,
    jobId: string
): Promise<{ job: SolverJob }> {
    const controller = getInjection('IGetJobController');
    const result = await controller({ caseId, monthYear, jobId });
    if ('error' in result) throw new Error('Job not found');
    return { job: result.data };
}

export async function getLastInsertedSolution(
    caseId: number,
    monthYear: string
): Promise<ActionResult<ScheduleSolutionRaw | null>> {
    const controller = getInjection('IGetLastInsertedSolutionController');
    const result = await controller({ caseId, monthYear });
    if ('error' in result) return { success: false, error: result.error };
    return { success: true, data: result.data };
}

export async function getSolverProgress(): Promise<ActionResult<SolverProgress | null>> {
    const controller = getInjection('IGetSolverProgressController');
    const result = await controller();
    if ('error' in result) return { success: false, error: result.error };
    return { success: true, data: result.data };
}
