import { ISolverService, SolverHealthResult } from "@/application/ports/solver.service";

export interface ICheckSolverHealthUseCase {
  (): Promise<SolverHealthResult>;
}

export function makeCheckSolverHealthUseCase(solverService: ISolverService): ICheckSolverHealthUseCase {
  return async () => {
    return await solverService.checkHealth();
  };
}
