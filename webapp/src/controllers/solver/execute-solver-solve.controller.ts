import { z } from 'zod';
import { isDomainError } from '@/entities/errors/base.errors';
import { validateMonthYear } from '@/entities/validation/input-validators';
import { SolveParamsSchema } from '@/entities/models/solver.model';
import type { SolverJob } from '@/entities/models/solver.model';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';
import type { IExecuteSolverSolveUseCase } from '@/application/use-cases/solver/execute-solver-solve.use-case';

const InputSchema = z.object({
    caseId: z.number().int().positive(),
    monthYear: z.string(),
    params: SolveParamsSchema,
});

export interface IExecuteSolverSolveController {
    (input: {
        caseId: number;
        monthYear: string;
        params: z.infer<typeof SolveParamsSchema>;
    }): Promise<{ data: { job: SolverJob; solution: ScheduleSolutionRaw } } | { error: string }>;
}

export function makeExecuteSolverSolveController(
    executeUseCase: IExecuteSolverSolveUseCase
): IExecuteSolverSolveController {
    return async (rawInput) => {
        try {
            const { caseId, monthYear, params } = InputSchema.parse(rawInput);
            validateMonthYear(monthYear);
            const result = await executeUseCase({ caseId, monthYear, params });
            return { data: result };
        } catch (error) {
            if (isDomainError(error)) return { error: error.message };
            if (error instanceof z.ZodError) return { error: error.issues[0]?.message ?? 'Invalid input' };
            if (error instanceof Error) return { error: error.message };
            throw error;
        }
    };
}
