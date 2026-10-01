import { isDomainError } from '@/entities/errors/base.errors';
import type { IGetSolverProgressUseCase } from '@/application/use-cases/solver/get-solver-progress.use-case';
import type { SolverProgress } from '@/application/ports/solver.service';

export interface IGetSolverProgressController {
    (): Promise<{ data: SolverProgress | null } | { error: string }>;
}

export function makeGetSolverProgressController(
    getProgressUseCase: IGetSolverProgressUseCase
): IGetSolverProgressController {
    return async () => {
        try {
            const data = await getProgressUseCase();
            return { data };
        } catch (error) {
            if (isDomainError(error)) return { error: error.message };
            if (error instanceof Error) return { error: error.message };
            throw error;
        }
    };
}
