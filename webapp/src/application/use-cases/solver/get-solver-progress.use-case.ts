import type { ISolverService, SolverProgress } from '@/application/ports/solver.service';

export interface IGetSolverProgressUseCase {
    (): Promise<SolverProgress | null>;
}

export function makeGetSolverProgressUseCase(
    solverService: ISolverService
): IGetSolverProgressUseCase {
    return async () => {
        return solverService.getProgress();
    };
}
