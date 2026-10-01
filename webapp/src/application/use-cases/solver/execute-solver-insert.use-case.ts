import { randomUUID } from 'crypto';
import type { ISolverService } from '@/application/ports/solver.service';
import type { IJobRepository } from '@/application/ports/job.repository';
import type { IScheduleRepository } from '@/application/ports/schedule.repository';
import type { InsertParams, SolverJob } from '@/entities/models/solver.model';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

export interface IExecuteSolverInsertUseCase {
    (input: {
        caseId: number;
        monthYear: string;
        params: InsertParams;
        solution?: ScheduleSolutionRaw; // API sends directly, CLI ignores it
    }): Promise<{ job: SolverJob }>;
}

export function makeExecuteSolverInsertUseCase(
    solverService: ISolverService,
    jobRepository: IJobRepository,
    scheduleRepository: IScheduleRepository,
): IExecuteSolverInsertUseCase {
    return async ({ caseId, monthYear, params, solution }) => {
        const startTime = Date.now();
        const result = await solverService.insertSolution(params, solution);

        const job: SolverJob = {
            id: randomUUID(),
            type: 'insert',
            status: result.success ? 'completed' : 'failed',
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
            throw new Error(`Insert failed: ${result.error}`);
        }

        // Persist which solution was inserted so delete can reference it later
        if (solution) {
            await scheduleRepository.saveLastInserted(caseId, monthYear, solution);
        }

        return { job };
    };
}
