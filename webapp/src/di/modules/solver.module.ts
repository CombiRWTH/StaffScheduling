import { createModule } from "@evyweb/ioctopus";
import { DI_SYMBOLS } from "@/di/types";
import { ScheduleParserService } from "@/lib/services/schedule-parser";
import { makeCheckSolverHealthUseCase } from "@/application/use-cases/solver/check-solver-health.use-case";
import { makeExecuteSolverFetchUseCase } from "@/application/use-cases/solver/execute-solver-fetch.use-case";
import { makeExecuteSolverSolveUseCase } from "@/application/use-cases/solver/execute-solver-solve.use-case";
import { makeExecuteSolverSolveMultipleUseCase } from "@/application/use-cases/solver/execute-solver-solve-multiple.use-case";
import { makeExecuteSolverInsertUseCase } from "@/application/use-cases/solver/execute-solver-insert.use-case";
import { makeExecuteSolverDeleteUseCase } from "@/application/use-cases/solver/execute-solver-delete.use-case";
import { makeImportSolutionUseCase } from "@/application/use-cases/solver/import-solution.use-case";
import { makeCheckSolverHealthController } from "@/controllers/solver/check-solver-health.controller";
import { makeExecuteSolverFetchController } from "@/controllers/solver/execute-solver-fetch.controller";
import { makeExecuteSolverSolveController } from "@/controllers/solver/execute-solver-solve.controller";
import { makeExecuteSolverSolveMultipleController } from "@/controllers/solver/execute-solver-solve-multiple.controller";
import { makeExecuteSolverInsertController } from "@/controllers/solver/execute-solver-insert.controller";
import { makeExecuteSolverDeleteController } from "@/controllers/solver/execute-solver-delete.controller";
import { makeImportSolutionController } from "@/controllers/solver/import-solution.controller";
import { SolverApiService } from "@/infrastructure/services/solver-api-service";
import { makeGetSolverProgressController } from "@/controllers/solver/get-solver-progress.controller";
import { makeGetSolverProgressUseCase } from "@/application/use-cases/solver/get-solver-progress.use-case";
import { makeGetLastInsertedSolutionUseCase } from "@/application/use-cases/solver/get-last-inserted-solution.use-case";
import { makeGetLastInsertedSolutionController } from "@/controllers/solver/get-last-inserted-solution.controller";

export function createSolverModule() {
  const m = createModule();

  // Infrastructure services
  m.bind(DI_SYMBOLS.ISolverService).toClass(SolverApiService, [], "singleton");

  m.bind(DI_SYMBOLS.IScheduleParserService).toClass(ScheduleParserService, [], "singleton");

  // Use Cases
  m.bind(DI_SYMBOLS.ICheckSolverHealthUseCase).toHigherOrderFunction(makeCheckSolverHealthUseCase, [
    DI_SYMBOLS.ISolverService,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverFetchUseCase).toHigherOrderFunction(makeExecuteSolverFetchUseCase, [
    DI_SYMBOLS.ISolverService,
    DI_SYMBOLS.IJobRepository,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverSolveUseCase).toHigherOrderFunction(makeExecuteSolverSolveUseCase, [
    DI_SYMBOLS.ISolverService,
    DI_SYMBOLS.IJobRepository,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverSolveMultipleUseCase).toHigherOrderFunction(makeExecuteSolverSolveMultipleUseCase, [
    DI_SYMBOLS.ISolverService,
    DI_SYMBOLS.IJobRepository,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverInsertUseCase).toHigherOrderFunction(makeExecuteSolverInsertUseCase, [
    DI_SYMBOLS.ISolverService,
    DI_SYMBOLS.IJobRepository,
    DI_SYMBOLS.IScheduleRepository,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverDeleteUseCase).toHigherOrderFunction(makeExecuteSolverDeleteUseCase, [
    DI_SYMBOLS.ISolverService,
    DI_SYMBOLS.IJobRepository,
    DI_SYMBOLS.IScheduleRepository,
  ]);
  m.bind(DI_SYMBOLS.IImportSolutionUseCase).toHigherOrderFunction(makeImportSolutionUseCase, [
    DI_SYMBOLS.IScheduleRepository,
  ]);

  // Controllers
  m.bind(DI_SYMBOLS.ICheckSolverHealthController).toHigherOrderFunction(makeCheckSolverHealthController, [
    DI_SYMBOLS.ICheckSolverHealthUseCase,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverFetchController).toHigherOrderFunction(makeExecuteSolverFetchController, [
    DI_SYMBOLS.IExecuteSolverFetchUseCase,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverSolveController).toHigherOrderFunction(makeExecuteSolverSolveController, [
    DI_SYMBOLS.IExecuteSolverSolveUseCase,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverSolveMultipleController).toHigherOrderFunction(
    makeExecuteSolverSolveMultipleController,
    [DI_SYMBOLS.IExecuteSolverSolveMultipleUseCase],
  );
  m.bind(DI_SYMBOLS.IExecuteSolverInsertController).toHigherOrderFunction(makeExecuteSolverInsertController, [
    DI_SYMBOLS.IExecuteSolverInsertUseCase,
  ]);
  m.bind(DI_SYMBOLS.IExecuteSolverDeleteController).toHigherOrderFunction(makeExecuteSolverDeleteController, [
    DI_SYMBOLS.IExecuteSolverDeleteUseCase,
  ]);
  m.bind(DI_SYMBOLS.IImportSolutionController).toHigherOrderFunction(makeImportSolutionController, [
    DI_SYMBOLS.IImportSolutionUseCase,
  ]);
  m.bind(DI_SYMBOLS.IGetSolverProgressController).toHigherOrderFunction(makeGetSolverProgressController, [
    DI_SYMBOLS.IGetSolverProgressUseCase,
  ]);
  m.bind(DI_SYMBOLS.IGetSolverProgressUseCase).toHigherOrderFunction(makeGetSolverProgressUseCase, [
    DI_SYMBOLS.ISolverService,
  ]);
  m.bind(DI_SYMBOLS.IGetLastInsertedSolutionUseCase).toHigherOrderFunction(makeGetLastInsertedSolutionUseCase, [
    DI_SYMBOLS.IScheduleRepository,
  ]);
  m.bind(DI_SYMBOLS.IGetLastInsertedSolutionController).toHigherOrderFunction(makeGetLastInsertedSolutionController, [
    DI_SYMBOLS.IGetLastInsertedSolutionUseCase,
  ]);

  return m;
}
