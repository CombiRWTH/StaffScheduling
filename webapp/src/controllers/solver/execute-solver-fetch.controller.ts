import {z} from 'zod';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';
import {FetchParamsSchema, SolverJob} from '@/entities/models/solver.model';
import type {IExecuteSolverFetchUseCase} from '@/application/use-cases/solver/execute-solver-fetch.use-case';

const InputSchema = z.object({
    caseId: z.number().int().positive(),
    monthYear: z.string(),
    params: FetchParamsSchema,
});

export interface IExecuteSolverFetchController {
    (input: {
        caseId: number;
        monthYear: string;
        params: z.infer<typeof FetchParamsSchema>;
    }): Promise<{ data: { job: SolverJob } } | { error: string }>;
}

export function makeExecuteSolverFetchController(
    executeUseCase: IExecuteSolverFetchUseCase
): IExecuteSolverFetchController {
    return async (rawInput) => {
        try {
            const {caseId, monthYear, params} = InputSchema.parse(rawInput);
            validateMonthYear(monthYear);
            const result = await executeUseCase({caseId, monthYear, params});
            return {data: result};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            if (error instanceof z.ZodError) return {error: error.issues[0]?.message ?? 'Invalid input'};
            if (error instanceof Error) return {error: error.message};
            throw error;
        }
    };
}
