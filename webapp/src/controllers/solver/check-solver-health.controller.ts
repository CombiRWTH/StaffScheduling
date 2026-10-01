import type {ICheckSolverHealthUseCase} from '@/application/use-cases/solver/check-solver-health.use-case';
import {isDomainError} from '@/entities/errors/base.errors';
import {SolverHealthResult} from "@/application/ports/solver.service";

export interface ICheckSolverHealthController {
    (): Promise<{ data: SolverHealthResult } | { error: string }>;
}

export function makeCheckSolverHealthController(
    checkSolverHealthUseCase: ICheckSolverHealthUseCase
): ICheckSolverHealthController {
    return async () => {
        try {
            const data = await checkSolverHealthUseCase();
            return {data};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            if (error instanceof Error) return {error: error.message};
            throw error;
        }
    };
}
