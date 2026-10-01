// Repository interfaces
import type { IWeightsRepository } from "@/application/ports/weights.repository";
import type { IMinimalStaffRepository } from "@/application/ports/minimal-staff.repository";
import type { IWishesAndBlockedRepository } from "@/application/ports/wishes-and-blocked.repository";
import type { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";
import type { IAvailabilityRepository } from "@/application/ports/availability.repository";
import type { IGlobalAvailabilityRepository } from "@/application/ports/global-availability.repository";
import type { IGlobalWishesTemplateRepository } from "@/application/ports/global-wishes-template.repository";
import type { IScheduleRepository } from "@/application/ports/schedule.repository";
import type { IJobRepository } from "@/application/ports/job.repository";
import type { ICaseRepository } from "@/application/ports/case.repository";
import type { IWeightsTemplateRepository } from "@/application/ports/weights-template.repository";
import type { IMinimalStaffTemplateRepository } from "@/application/ports/minimal-staff-template.repository";

// Service interfaces
import type { ISolverService } from "@/application/ports/solver.service";
import type { IScheduleParserService } from "@/application/ports/schedule-parser.service";

// Use Case interfaces
import type { IGetWeightsUseCase } from "@/application/use-cases/weights/get-weights.use-case";
import type { IUpdateWeightsUseCase } from "@/application/use-cases/weights/update-weights.use-case";
import type { IGetMinimalStaffUseCase } from "@/application/use-cases/minimal-staff/get-minimal-staff.use-case";
import type { IUpdateMinimalStaffUseCase } from "@/application/use-cases/minimal-staff/update-minimal-staff.use-case";
import type { IGetAllWishesUseCase } from "@/application/use-cases/wishes-and-blocked/get-all-wishes.use-case";
import type { IGetWishesByKeyUseCase } from "@/application/use-cases/wishes-and-blocked/get-wishes-by-key.use-case";
import type { ICreateWishesUseCase } from "@/application/use-cases/wishes-and-blocked/create-wishes.use-case";
import type { IUpdateWishesUseCase } from "@/application/use-cases/wishes-and-blocked/update-wishes.use-case";
import type { IDeleteWishesUseCase } from "@/application/use-cases/wishes-and-blocked/delete-wishes.use-case";
import type { IGetAllGlobalWishesUseCase } from "@/application/use-cases/global-wishes/get-all-global-wishes.use-case";
import type { IGetGlobalWishesByKeyUseCase } from "@/application/use-cases/global-wishes/get-global-wishes-by-key.use-case";
import type { ICreateGlobalWishesUseCase } from "@/application/use-cases/global-wishes/create-global-wishes.use-case";
import type { IUpdateGlobalWishesUseCase } from "@/application/use-cases/global-wishes/update-global-wishes.use-case";
import type { IDeleteGlobalWishesUseCase } from "@/application/use-cases/global-wishes/delete-global-wishes.use-case";
import type { IImportGlobalWishesTemplateUseCase } from "@/application/use-cases/global-wishes/import-global-wishes-template.use-case";
import type { IGetAllAvailabilityUseCase } from "@/application/use-cases/availability/get-all-availability.use-case";
import type { IGetAvailabilityByKeyUseCase } from "@/application/use-cases/availability/get-availability-by-key.use-case";
import type { ICreateAvailabilityUseCase } from "@/application/use-cases/availability/create-availability.use-case";
import type { IUpdateAvailabilityUseCase } from "@/application/use-cases/availability/update-availability.use-case";
import type { IDeleteAvailabilityUseCase } from "@/application/use-cases/availability/delete-availability.use-case";
import type { IGetAllGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/get-all-global-availability.use-case";
import type { IGetGlobalAvailabilityByKeyUseCase } from "@/application/use-cases/global-availability/get-global-availability-by-key.use-case";
import type { ICreateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/create-global-availability.use-case";
import type { IUpdateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/update-global-availability.use-case";
import type { IDeleteGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/delete-global-availability.use-case";
import type { IGetSchedulesMetadataUseCase } from "@/application/use-cases/schedule/get-schedules-metadata.use-case";
import type { IGetScheduleUseCase } from "@/application/use-cases/schedule/get-schedule.use-case";
import type { ISaveScheduleUseCase } from "@/application/use-cases/schedule/save-schedule.use-case";
import type { IDeleteScheduleUseCase } from "@/application/use-cases/schedule/delete-schedule.use-case";
import type { ISelectScheduleUseCase } from "@/application/use-cases/schedule/select-schedule.use-case";
import type { IUpdateScheduleMetadataUseCase } from "@/application/use-cases/schedule/update-schedule-metadata.use-case";
import type { IGetAllJobsUseCase } from "@/application/use-cases/jobs/get-all-jobs.use-case";
import type { IGetJobUseCase } from "@/application/use-cases/jobs/get-job.use-case";
import type { ICreateJobUseCase } from "@/application/use-cases/jobs/create-job.use-case";
import type { IListCasesUseCase } from "@/application/use-cases/cases/list-cases.use-case";
import type { IGetSelectedScheduleUseCase } from "@/application/use-cases/schedule/get-selected-schedule.use-case";
// Use Case interfaces — Weights Templates
import type { IListWeightsTemplatesUseCase } from "@/application/use-cases/templates/weights/list-weights-templates.use-case";
import type { IGetWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/get-weights-template.use-case";
import type { ICreateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/create-weights-template.use-case";
import type { IUpdateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/update-weights-template.use-case";
import type { IDeleteWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/delete-weights-template.use-case";
// Use Case interfaces — Minimal Staff Templates
import type { IListMinimalStaffTemplatesUseCase } from "@/application/use-cases/templates/minimal-staff/list-minimal-staff-templates.use-case";
import type { IGetMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/get-minimal-staff-template.use-case";
import type { ICreateMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/create-minimal-staff-template.use-case";
import type { IUpdateMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/update-minimal-staff-template.use-case";
import type { IDeleteMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/delete-minimal-staff-template.use-case";
// Use Case interfaces — Global Wishes Templates
import type { IListGlobalWishesTemplatesUseCase } from "@/application/use-cases/templates/global-wishes/list-global-wishes-templates.use-case";
import type { IGetGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/get-global-wishes-template.use-case";
import type { ICreateGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/create-global-wishes-template.use-case";
import type { IUpdateGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/update-global-wishes-template.use-case";
import type { IDeleteGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/delete-global-wishes-template.use-case";

// Use Case interfaces — Solver
import type { ICheckSolverHealthUseCase } from "@/application/use-cases/solver/check-solver-health.use-case";
import type { IExecuteSolverFetchUseCase } from "@/application/use-cases/solver/execute-solver-fetch.use-case";
import type { IExecuteSolverSolveUseCase } from "@/application/use-cases/solver/execute-solver-solve.use-case";
import type { IExecuteSolverSolveMultipleUseCase } from "@/application/use-cases/solver/execute-solver-solve-multiple.use-case";
import type { IExecuteSolverInsertUseCase } from "@/application/use-cases/solver/execute-solver-insert.use-case";
import type { IExecuteSolverDeleteUseCase } from "@/application/use-cases/solver/execute-solver-delete.use-case";
import type { IImportSolutionUseCase } from "@/application/use-cases/solver/import-solution.use-case";

// Controller interfaces
import type { IGetWeightsController } from "@/controllers/weights/get-weights.controller";
import type { IUpdateWeightsController } from "@/controllers/weights/update-weights.controller";
import type { IGetMinimalStaffController } from "@/controllers/minimal-staff/get-minimal-staff.controller";
import type { IUpdateMinimalStaffController } from "@/controllers/minimal-staff/update-minimal-staff.controller";
import type { IGetAllWishesController } from "@/controllers/wishes-and-blocked/get-all-wishes.controller";
import type { IGetWishesByKeyController } from "@/controllers/wishes-and-blocked/get-wishes-by-key.controller";
import type { ICreateWishesController } from "@/controllers/wishes-and-blocked/create-wishes.controller";
import type { IUpdateWishesController } from "@/controllers/wishes-and-blocked/update-wishes.controller";
import type { IDeleteWishesController } from "@/controllers/wishes-and-blocked/delete-wishes.controller";
import type { IGetAllGlobalWishesController } from "@/controllers/global-wishes/get-all-global-wishes.controller";
import type { IGetGlobalWishesByKeyController } from "@/controllers/global-wishes/get-global-wishes-by-key.controller";
import type { ICreateGlobalWishesController } from "@/controllers/global-wishes/create-global-wishes.controller";
import type { IUpdateGlobalWishesController } from "@/controllers/global-wishes/update-global-wishes.controller";
import type { IDeleteGlobalWishesController } from "@/controllers/global-wishes/delete-global-wishes.controller";
import type { IImportGlobalWishesTemplateController } from "@/controllers/global-wishes/import-global-wishes-template.controller";
import type { IGetAllAvailabilityController } from "@/controllers/availability/get-all-availability.controller";
import type { IGetAvailabilityByKeyController } from "@/controllers/availability/get-availability-by-key.controller";
import type { ICreateAvailabilityController } from "@/controllers/availability/create-availability.controller";
import type { IUpdateAvailabilityController } from "@/controllers/availability/update-availability.controller";
import type { IDeleteAvailabilityController } from "@/controllers/availability/delete-availability.controller";
import type { IGetAllGlobalAvailabilityController } from "@/controllers/global-availability/get-all-global-availability.controller";
import type { IGetGlobalAvailabilityByKeyController } from "@/controllers/global-availability/get-global-availability-by-key.controller";
import type { ICreateGlobalAvailabilityController } from "@/controllers/global-availability/create-global-availability.controller";
import type { IUpdateGlobalAvailabilityController } from "@/controllers/global-availability/update-global-availability.controller";
import type { IDeleteGlobalAvailabilityController } from "@/controllers/global-availability/delete-global-availability.controller";
import type { IGetSchedulesMetadataController } from "@/controllers/schedule/get-schedules-metadata.controller";
import type { IGetScheduleController } from "@/controllers/schedule/get-schedule.controller";
import type { ISaveScheduleController } from "@/controllers/schedule/save-schedule.controller";
import type { IDeleteScheduleController } from "@/controllers/schedule/delete-schedule.controller";
import type { ISelectScheduleController } from "@/controllers/schedule/select-schedule.controller";
import type { IUpdateScheduleMetadataController } from "@/controllers/schedule/update-schedule-metadata.controller";
import type { IGetAllJobsController } from "@/controllers/jobs/get-all-jobs.controller";
import type { IGetJobController } from "@/controllers/jobs/get-job.controller";
import type { ICreateJobController } from "@/controllers/jobs/create-job.controller";
import type { IListCasesController } from "@/controllers/cases/list-cases.controller";
import type { IGetSelectedScheduleController } from "@/controllers/schedule/get-selected-schedule.controller";
// Controller interfaces — Weights Templates
import type { IListWeightsTemplatesController } from "@/controllers/templates/weights/list-weights-templates.controller";
import type { IGetWeightsTemplateController } from "@/controllers/templates/weights/get-weights-template.controller";
import type { ICreateWeightsTemplateController } from "@/controllers/templates/weights/create-weights-template.controller";
import type { IUpdateWeightsTemplateController } from "@/controllers/templates/weights/update-weights-template.controller";
import type { IDeleteWeightsTemplateController } from "@/controllers/templates/weights/delete-weights-template.controller";
// Controller interfaces — Minimal Staff Templates
import type { IListMinimalStaffTemplatesController } from "@/controllers/templates/minimal-staff/list-minimal-staff-templates.controller";
import type { IGetMinimalStaffTemplateController } from "@/controllers/templates/minimal-staff/get-minimal-staff-template.controller";
import type { ICreateMinimalStaffTemplateController } from "@/controllers/templates/minimal-staff/create-minimal-staff-template.controller";
import type { IUpdateMinimalStaffTemplateController } from "@/controllers/templates/minimal-staff/update-minimal-staff-template.controller";
import type { IDeleteMinimalStaffTemplateController } from "@/controllers/templates/minimal-staff/delete-minimal-staff-template.controller";
// Controller interfaces — Global Wishes Templates
import type { IListGlobalWishesTemplatesController } from "@/controllers/templates/global-wishes/list-global-wishes-templates.controller";
import type { IGetGlobalWishesTemplateController } from "@/controllers/templates/global-wishes/get-global-wishes-template.controller";
import type { ICreateGlobalWishesTemplateController } from "@/controllers/templates/global-wishes/create-global-wishes-template.controller";
import type { IUpdateGlobalWishesTemplateController } from "@/controllers/templates/global-wishes/update-global-wishes-template.controller";
import type { IDeleteGlobalWishesTemplateController } from "@/controllers/templates/global-wishes/delete-global-wishes-template.controller";

// Controller interfaces — Solver
import type { ICheckSolverHealthController } from "@/controllers/solver/check-solver-health.controller";
import type { IExecuteSolverFetchController } from "@/controllers/solver/execute-solver-fetch.controller";
import type { IExecuteSolverSolveController } from "@/controllers/solver/execute-solver-solve.controller";
import type { IExecuteSolverSolveMultipleController } from "@/controllers/solver/execute-solver-solve-multiple.controller";
import type { IExecuteSolverInsertController } from "@/controllers/solver/execute-solver-insert.controller";
import type { IExecuteSolverDeleteController } from "@/controllers/solver/execute-solver-delete.controller";
import type { IImportSolutionController } from "@/controllers/solver/import-solution.controller";
import type { IGetSolverProgressUseCase } from "@/application/use-cases/solver/get-solver-progress.use-case";
import type { IGetSolverProgressController } from "@/controllers/solver/get-solver-progress.controller";
import type { IGetLastInsertedSolutionUseCase } from "@/application/use-cases/solver/get-last-inserted-solution.use-case";
import type { IGetLastInsertedSolutionController } from "@/controllers/solver/get-last-inserted-solution.controller";

export const DI_SYMBOLS = {
  // Repositories
  IWeightsRepository: Symbol.for("IWeightsRepository"),
  IMinimalStaffRepository: Symbol.for("IMinimalStaffRepository"),
  IWishesAndBlockedRepository: Symbol.for("IWishesAndBlockedRepository"),
  IGlobalWishesAndBlockedRepository: Symbol.for("IGlobalWishesAndBlockedRepository"),
  IAvailabilityRepository: Symbol.for("IAvailabilityRepository"),
  IGlobalAvailabilityRepository: Symbol.for("IGlobalAvailabilityRepository"),
  IGlobalWishesTemplateRepository: Symbol.for("IGlobalWishesTemplateRepository"),
  IWeightsTemplateRepository: Symbol.for("IWeightsTemplateRepository"),
  IMinimalStaffTemplateRepository: Symbol.for("IMinimalStaffTemplateRepository"),
  IScheduleRepository: Symbol.for("IScheduleRepository"),
  IJobRepository: Symbol.for("IJobRepository"),
  ICaseRepository: Symbol.for("ICaseRepository"),

  // Use Cases — Employees

  // Use Cases — Weights
  IGetWeightsUseCase: Symbol.for("IGetWeightsUseCase"),
  IUpdateWeightsUseCase: Symbol.for("IUpdateWeightsUseCase"),

  // Use Cases — Minimal Staff
  IGetMinimalStaffUseCase: Symbol.for("IGetMinimalStaffUseCase"),
  IUpdateMinimalStaffUseCase: Symbol.for("IUpdateMinimalStaffUseCase"),

  // Use Cases — Wishes and Blocked
  IGetAllWishesUseCase: Symbol.for("IGetAllWishesUseCase"),
  IGetWishesByKeyUseCase: Symbol.for("IGetWishesByKeyUseCase"),
  ICreateWishesUseCase: Symbol.for("ICreateWishesUseCase"),
  IUpdateWishesUseCase: Symbol.for("IUpdateWishesUseCase"),
  IDeleteWishesUseCase: Symbol.for("IDeleteWishesUseCase"),

  // Use Cases — Global Wishes
  IGetAllGlobalWishesUseCase: Symbol.for("IGetAllGlobalWishesUseCase"),
  IGetGlobalWishesByKeyUseCase: Symbol.for("IGetGlobalWishesByKeyUseCase"),
  ICreateGlobalWishesUseCase: Symbol.for("ICreateGlobalWishesUseCase"),
  IUpdateGlobalWishesUseCase: Symbol.for("IUpdateGlobalWishesUseCase"),
  IDeleteGlobalWishesUseCase: Symbol.for("IDeleteGlobalWishesUseCase"),
  IImportGlobalWishesTemplateUseCase: Symbol.for("IImportGlobalWishesTemplateUseCase"),

  // Use Cases — Availability
  IGetAllAvailabilityUseCase: Symbol.for("IGetAllAvailabilityUseCase"),
  IGetAvailabilityByKeyUseCase: Symbol.for("IGetAvailabilityByKeyUseCase"),
  ICreateAvailabilityUseCase: Symbol.for("ICreateAvailabilityUseCase"),
  IUpdateAvailabilityUseCase: Symbol.for("IUpdateAvailabilityUseCase"),
  IDeleteAvailabilityUseCase: Symbol.for("IDeleteAvailabilityUseCase"),

  // Use Cases — Global Availability
  IGetAllGlobalAvailabilityUseCase: Symbol.for("IGetAllGlobalAvailabilityUseCase"),
  IGetGlobalAvailabilityByKeyUseCase: Symbol.for("IGetGlobalAvailabilityByKeyUseCase"),
  ICreateGlobalAvailabilityUseCase: Symbol.for("ICreateGlobalAvailabilityUseCase"),
  IUpdateGlobalAvailabilityUseCase: Symbol.for("IUpdateGlobalAvailabilityUseCase"),
  IDeleteGlobalAvailabilityUseCase: Symbol.for("IDeleteGlobalAvailabilityUseCase"),

  // Use Cases — Schedule
  IGetSchedulesMetadataUseCase: Symbol.for("IGetSchedulesMetadataUseCase"),
  IGetScheduleUseCase: Symbol.for("IGetScheduleUseCase"),
  ISaveScheduleUseCase: Symbol.for("ISaveScheduleUseCase"),
  IDeleteScheduleUseCase: Symbol.for("IDeleteScheduleUseCase"),
  ISelectScheduleUseCase: Symbol.for("ISelectScheduleUseCase"),
  IUpdateScheduleMetadataUseCase: Symbol.for("IUpdateScheduleMetadataUseCase"),

  // Use Cases — Jobs
  IGetAllJobsUseCase: Symbol.for("IGetAllJobsUseCase"),
  IGetJobUseCase: Symbol.for("IGetJobUseCase"),
  ICreateJobUseCase: Symbol.for("ICreateJobUseCase"),

  // Use Cases — Cases
  IListCasesUseCase: Symbol.for("IListCasesUseCase"),

  // Use Cases — Schedule (extended)
  IGetSelectedScheduleUseCase: Symbol.for("IGetSelectedScheduleUseCase"),

  // Use Cases — Weights Templates
  IListWeightsTemplatesUseCase: Symbol.for("IListWeightsTemplatesUseCase"),
  IGetWeightsTemplateUseCase: Symbol.for("IGetWeightsTemplateUseCase"),
  ICreateWeightsTemplateUseCase: Symbol.for("ICreateWeightsTemplateUseCase"),
  IUpdateWeightsTemplateUseCase: Symbol.for("IUpdateWeightsTemplateUseCase"),
  IDeleteWeightsTemplateUseCase: Symbol.for("IDeleteWeightsTemplateUseCase"),

  // Use Cases — Minimal Staff Templates
  IListMinimalStaffTemplatesUseCase: Symbol.for("IListMinimalStaffTemplatesUseCase"),
  IGetMinimalStaffTemplateUseCase: Symbol.for("IGetMinimalStaffTemplateUseCase"),
  ICreateMinimalStaffTemplateUseCase: Symbol.for("ICreateMinimalStaffTemplateUseCase"),
  IUpdateMinimalStaffTemplateUseCase: Symbol.for("IUpdateMinimalStaffTemplateUseCase"),
  IDeleteMinimalStaffTemplateUseCase: Symbol.for("IDeleteMinimalStaffTemplateUseCase"),

  // Use Cases — Global Wishes Templates
  IListGlobalWishesTemplatesUseCase: Symbol.for("IListGlobalWishesTemplatesUseCase"),
  IGetGlobalWishesTemplateUseCase: Symbol.for("IGetGlobalWishesTemplateUseCase"),
  ICreateGlobalWishesTemplateUseCase: Symbol.for("ICreateGlobalWishesTemplateUseCase"),
  IUpdateGlobalWishesTemplateUseCase: Symbol.for("IUpdateGlobalWishesTemplateUseCase"),
  IDeleteGlobalWishesTemplateUseCase: Symbol.for("IDeleteGlobalWishesTemplateUseCase"),

  // Services — Solver
  ISolverService: Symbol.for("ISolverService"),
  IScheduleParserService: Symbol.for("IScheduleParserService"),

  // Use Cases — Solver
  ICheckSolverHealthUseCase: Symbol.for("ICheckSolverHealthUseCase"),
  IExecuteSolverFetchUseCase: Symbol.for("IExecuteSolverFetchUseCase"),
  IExecuteSolverSolveUseCase: Symbol.for("IExecuteSolverSolveUseCase"),
  IExecuteSolverSolveMultipleUseCase: Symbol.for("IExecuteSolverSolveMultipleUseCase"),
  IExecuteSolverInsertUseCase: Symbol.for("IExecuteSolverInsertUseCase"),
  IExecuteSolverDeleteUseCase: Symbol.for("IExecuteSolverDeleteUseCase"),
  IImportSolutionUseCase: Symbol.for("IImportSolutionUseCase"),
  IGetSolverProgressUseCase: Symbol.for("IGetSolverProgressUseCase"),
  IGetLastInsertedSolutionUseCase: Symbol.for("IGetLastInsertedSolutionUseCase"),

  // Controllers — Employees

  // Controllers — Weights
  IGetWeightsController: Symbol.for("IGetWeightsController"),
  IUpdateWeightsController: Symbol.for("IUpdateWeightsController"),

  // Controllers — Minimal Staff
  IGetMinimalStaffController: Symbol.for("IGetMinimalStaffController"),
  IUpdateMinimalStaffController: Symbol.for("IUpdateMinimalStaffController"),

  // Controllers — Wishes and Blocked
  IGetAllWishesController: Symbol.for("IGetAllWishesController"),
  IGetWishesByKeyController: Symbol.for("IGetWishesByKeyController"),
  ICreateWishesController: Symbol.for("ICreateWishesController"),
  IUpdateWishesController: Symbol.for("IUpdateWishesController"),
  IDeleteWishesController: Symbol.for("IDeleteWishesController"),

  // Controllers — Global Wishes
  IGetAllGlobalWishesController: Symbol.for("IGetAllGlobalWishesController"),
  IGetGlobalWishesByKeyController: Symbol.for("IGetGlobalWishesByKeyController"),
  ICreateGlobalWishesController: Symbol.for("ICreateGlobalWishesController"),
  IUpdateGlobalWishesController: Symbol.for("IUpdateGlobalWishesController"),
  IDeleteGlobalWishesController: Symbol.for("IDeleteGlobalWishesController"),
  IImportGlobalWishesTemplateController: Symbol.for("IImportGlobalWishesTemplateController"),

  // Controllers — Availability
  IGetAllAvailabilityController: Symbol.for("IGetAllAvailabilityController"),
  IGetAvailabilityByKeyController: Symbol.for("IGetAvailabilityByKeyController"),
  ICreateAvailabilityController: Symbol.for("ICreateAvailabilityController"),
  IUpdateAvailabilityController: Symbol.for("IUpdateAvailabilityController"),
  IDeleteAvailabilityController: Symbol.for("IDeleteAvailabilityController"),

  // Controllers — Global Availability
  IGetAllGlobalAvailabilityController: Symbol.for("IGetAllGlobalAvailabilityController"),
  IGetGlobalAvailabilityByKeyController: Symbol.for("IGetGlobalAvailabilityByKeyController"),
  ICreateGlobalAvailabilityController: Symbol.for("ICreateGlobalAvailabilityController"),
  IUpdateGlobalAvailabilityController: Symbol.for("IUpdateGlobalAvailabilityController"),
  IDeleteGlobalAvailabilityController: Symbol.for("IDeleteGlobalAvailabilityController"),

  // Controllers — Schedule
  IGetSchedulesMetadataController: Symbol.for("IGetSchedulesMetadataController"),
  IGetScheduleController: Symbol.for("IGetScheduleController"),
  ISaveScheduleController: Symbol.for("ISaveScheduleController"),
  IDeleteScheduleController: Symbol.for("IDeleteScheduleController"),
  ISelectScheduleController: Symbol.for("ISelectScheduleController"),
  IUpdateScheduleMetadataController: Symbol.for("IUpdateScheduleMetadataController"),

  // Controllers — Jobs
  IGetAllJobsController: Symbol.for("IGetAllJobsController"),
  IGetJobController: Symbol.for("IGetJobController"),
  ICreateJobController: Symbol.for("ICreateJobController"),

  // Controllers — Cases
  IListCasesController: Symbol.for("IListCasesController"),

  // Controllers — Schedule (extended)
  IGetSelectedScheduleController: Symbol.for("IGetSelectedScheduleController"),

  // Controllers — Weights Templates
  IListWeightsTemplatesController: Symbol.for("IListWeightsTemplatesController"),
  IGetWeightsTemplateController: Symbol.for("IGetWeightsTemplateController"),
  ICreateWeightsTemplateController: Symbol.for("ICreateWeightsTemplateController"),
  IUpdateWeightsTemplateController: Symbol.for("IUpdateWeightsTemplateController"),
  IDeleteWeightsTemplateController: Symbol.for("IDeleteWeightsTemplateController"),

  // Controllers — Minimal Staff Templates
  IListMinimalStaffTemplatesController: Symbol.for("IListMinimalStaffTemplatesController"),
  IGetMinimalStaffTemplateController: Symbol.for("IGetMinimalStaffTemplateController"),
  ICreateMinimalStaffTemplateController: Symbol.for("ICreateMinimalStaffTemplateController"),
  IUpdateMinimalStaffTemplateController: Symbol.for("IUpdateMinimalStaffTemplateController"),
  IDeleteMinimalStaffTemplateController: Symbol.for("IDeleteMinimalStaffTemplateController"),

  // Controllers — Global Wishes Templates
  IListGlobalWishesTemplatesController: Symbol.for("IListGlobalWishesTemplatesController"),
  IGetGlobalWishesTemplateController: Symbol.for("IGetGlobalWishesTemplateController"),
  ICreateGlobalWishesTemplateController: Symbol.for("ICreateGlobalWishesTemplateController"),
  IUpdateGlobalWishesTemplateController: Symbol.for("IUpdateGlobalWishesTemplateController"),
  IDeleteGlobalWishesTemplateController: Symbol.for("IDeleteGlobalWishesTemplateController"),

  // Controllers — Solver
  ICheckSolverHealthController: Symbol.for("ICheckSolverHealthController"),
  IExecuteSolverFetchController: Symbol.for("IExecuteSolverFetchController"),
  IExecuteSolverSolveController: Symbol.for("IExecuteSolverSolveController"),
  IExecuteSolverSolveMultipleController: Symbol.for("IExecuteSolverSolveMultipleController"),
  IExecuteSolverInsertController: Symbol.for("IExecuteSolverInsertController"),
  IExecuteSolverDeleteController: Symbol.for("IExecuteSolverDeleteController"),
  IImportSolutionController: Symbol.for("IImportSolutionController"),
  IGetSolverProgressController: Symbol.for("IGetSolverProgressController"),
  IGetLastInsertedSolutionController: Symbol.for("IGetLastInsertedSolutionController"),
} as const;

export interface DI_RETURN_TYPES {
  // Repositories
  IWeightsRepository: IWeightsRepository;
  IMinimalStaffRepository: IMinimalStaffRepository;
  IWishesAndBlockedRepository: IWishesAndBlockedRepository;
  IGlobalWishesAndBlockedRepository: IGlobalWishesAndBlockedRepository;
  IAvailabilityRepository: IAvailabilityRepository;
  IGlobalAvailabilityRepository: IGlobalAvailabilityRepository;
  IGlobalWishesTemplateRepository: IGlobalWishesTemplateRepository;
  IWeightsTemplateRepository: IWeightsTemplateRepository;
  IMinimalStaffTemplateRepository: IMinimalStaffTemplateRepository;
  IScheduleRepository: IScheduleRepository;
  IJobRepository: IJobRepository;
  ICaseRepository: ICaseRepository;

  // Use Cases — Employees

  // Use Cases — Weights
  IGetWeightsUseCase: IGetWeightsUseCase;
  IUpdateWeightsUseCase: IUpdateWeightsUseCase;

  // Use Cases — Minimal Staff
  IGetMinimalStaffUseCase: IGetMinimalStaffUseCase;
  IUpdateMinimalStaffUseCase: IUpdateMinimalStaffUseCase;

  // Use Cases — Wishes and Blocked
  IGetAllWishesUseCase: IGetAllWishesUseCase;
  IGetWishesByKeyUseCase: IGetWishesByKeyUseCase;
  ICreateWishesUseCase: ICreateWishesUseCase;
  IUpdateWishesUseCase: IUpdateWishesUseCase;
  IDeleteWishesUseCase: IDeleteWishesUseCase;

  // Use Cases — Global Wishes
  IGetAllGlobalWishesUseCase: IGetAllGlobalWishesUseCase;
  IGetGlobalWishesByKeyUseCase: IGetGlobalWishesByKeyUseCase;
  ICreateGlobalWishesUseCase: ICreateGlobalWishesUseCase;
  IUpdateGlobalWishesUseCase: IUpdateGlobalWishesUseCase;
  IDeleteGlobalWishesUseCase: IDeleteGlobalWishesUseCase;
  IImportGlobalWishesTemplateUseCase: IImportGlobalWishesTemplateUseCase;

  // Use Cases — Availability
  IGetAllAvailabilityUseCase: IGetAllAvailabilityUseCase;
  IGetAvailabilityByKeyUseCase: IGetAvailabilityByKeyUseCase;
  ICreateAvailabilityUseCase: ICreateAvailabilityUseCase;
  IUpdateAvailabilityUseCase: IUpdateAvailabilityUseCase;
  IDeleteAvailabilityUseCase: IDeleteAvailabilityUseCase;

  // Use Cases — Global Availability
  IGetAllGlobalAvailabilityUseCase: IGetAllGlobalAvailabilityUseCase;
  IGetGlobalAvailabilityByKeyUseCase: IGetGlobalAvailabilityByKeyUseCase;
  ICreateGlobalAvailabilityUseCase: ICreateGlobalAvailabilityUseCase;
  IUpdateGlobalAvailabilityUseCase: IUpdateGlobalAvailabilityUseCase;
  IDeleteGlobalAvailabilityUseCase: IDeleteGlobalAvailabilityUseCase;

  // Use Cases — Schedule
  IGetSchedulesMetadataUseCase: IGetSchedulesMetadataUseCase;
  IGetScheduleUseCase: IGetScheduleUseCase;
  ISaveScheduleUseCase: ISaveScheduleUseCase;
  IDeleteScheduleUseCase: IDeleteScheduleUseCase;
  ISelectScheduleUseCase: ISelectScheduleUseCase;
  IUpdateScheduleMetadataUseCase: IUpdateScheduleMetadataUseCase;

  // Use Cases — Jobs
  IGetAllJobsUseCase: IGetAllJobsUseCase;
  IGetJobUseCase: IGetJobUseCase;
  ICreateJobUseCase: ICreateJobUseCase;

  // Use Cases — Cases
  IListCasesUseCase: IListCasesUseCase;

  // Use Cases — Schedule (extended)
  IGetSelectedScheduleUseCase: IGetSelectedScheduleUseCase;

  // Use Cases — Weights Templates
  IListWeightsTemplatesUseCase: IListWeightsTemplatesUseCase;
  IGetWeightsTemplateUseCase: IGetWeightsTemplateUseCase;
  ICreateWeightsTemplateUseCase: ICreateWeightsTemplateUseCase;
  IUpdateWeightsTemplateUseCase: IUpdateWeightsTemplateUseCase;
  IDeleteWeightsTemplateUseCase: IDeleteWeightsTemplateUseCase;

  // Use Cases — Minimal Staff Templates
  IListMinimalStaffTemplatesUseCase: IListMinimalStaffTemplatesUseCase;
  IGetMinimalStaffTemplateUseCase: IGetMinimalStaffTemplateUseCase;
  ICreateMinimalStaffTemplateUseCase: ICreateMinimalStaffTemplateUseCase;
  IUpdateMinimalStaffTemplateUseCase: IUpdateMinimalStaffTemplateUseCase;
  IDeleteMinimalStaffTemplateUseCase: IDeleteMinimalStaffTemplateUseCase;

  // Use Cases — Global Wishes Templates
  IListGlobalWishesTemplatesUseCase: IListGlobalWishesTemplatesUseCase;
  IGetGlobalWishesTemplateUseCase: IGetGlobalWishesTemplateUseCase;
  ICreateGlobalWishesTemplateUseCase: ICreateGlobalWishesTemplateUseCase;
  IUpdateGlobalWishesTemplateUseCase: IUpdateGlobalWishesTemplateUseCase;
  IDeleteGlobalWishesTemplateUseCase: IDeleteGlobalWishesTemplateUseCase;

  // Services — Solver
  ISolverService: ISolverService;
  IScheduleParserService: IScheduleParserService;

  // Use Cases — Solver
  ICheckSolverHealthUseCase: ICheckSolverHealthUseCase;
  IExecuteSolverFetchUseCase: IExecuteSolverFetchUseCase;
  IExecuteSolverSolveUseCase: IExecuteSolverSolveUseCase;
  IExecuteSolverSolveMultipleUseCase: IExecuteSolverSolveMultipleUseCase;
  IExecuteSolverInsertUseCase: IExecuteSolverInsertUseCase;
  IExecuteSolverDeleteUseCase: IExecuteSolverDeleteUseCase;
  IImportSolutionUseCase: IImportSolutionUseCase;
  IGetSolverProgressUseCase: IGetSolverProgressUseCase;
  IGetLastInsertedSolutionUseCase: IGetLastInsertedSolutionUseCase;

  // Controllers — Employees

  // Controllers — Weights
  IGetWeightsController: IGetWeightsController;
  IUpdateWeightsController: IUpdateWeightsController;

  // Controllers — Minimal Staff
  IGetMinimalStaffController: IGetMinimalStaffController;
  IUpdateMinimalStaffController: IUpdateMinimalStaffController;

  // Controllers — Wishes and Blocked
  IGetAllWishesController: IGetAllWishesController;
  IGetWishesByKeyController: IGetWishesByKeyController;
  ICreateWishesController: ICreateWishesController;
  IUpdateWishesController: IUpdateWishesController;
  IDeleteWishesController: IDeleteWishesController;

  // Controllers — Global Wishes
  IGetAllGlobalWishesController: IGetAllGlobalWishesController;
  IGetGlobalWishesByKeyController: IGetGlobalWishesByKeyController;
  ICreateGlobalWishesController: ICreateGlobalWishesController;
  IUpdateGlobalWishesController: IUpdateGlobalWishesController;
  IDeleteGlobalWishesController: IDeleteGlobalWishesController;
  IImportGlobalWishesTemplateController: IImportGlobalWishesTemplateController;

  // Controllers — Availability
  IGetAllAvailabilityController: IGetAllAvailabilityController;
  IGetAvailabilityByKeyController: IGetAvailabilityByKeyController;
  ICreateAvailabilityController: ICreateAvailabilityController;
  IUpdateAvailabilityController: IUpdateAvailabilityController;
  IDeleteAvailabilityController: IDeleteAvailabilityController;

  // Controllers — Global Availability
  IGetAllGlobalAvailabilityController: IGetAllGlobalAvailabilityController;
  IGetGlobalAvailabilityByKeyController: IGetGlobalAvailabilityByKeyController;
  ICreateGlobalAvailabilityController: ICreateGlobalAvailabilityController;
  IUpdateGlobalAvailabilityController: IUpdateGlobalAvailabilityController;
  IDeleteGlobalAvailabilityController: IDeleteGlobalAvailabilityController;

  // Controllers — Schedule
  IGetSchedulesMetadataController: IGetSchedulesMetadataController;
  IGetScheduleController: IGetScheduleController;
  ISaveScheduleController: ISaveScheduleController;
  IDeleteScheduleController: IDeleteScheduleController;
  ISelectScheduleController: ISelectScheduleController;
  IUpdateScheduleMetadataController: IUpdateScheduleMetadataController;

  // Controllers — Jobs
  IGetAllJobsController: IGetAllJobsController;
  IGetJobController: IGetJobController;
  ICreateJobController: ICreateJobController;

  // Controllers — Cases
  IListCasesController: IListCasesController;

  // Controllers — Schedule (extended)
  IGetSelectedScheduleController: IGetSelectedScheduleController;

  // Controllers — Weights Templates
  IListWeightsTemplatesController: IListWeightsTemplatesController;
  IGetWeightsTemplateController: IGetWeightsTemplateController;
  ICreateWeightsTemplateController: ICreateWeightsTemplateController;
  IUpdateWeightsTemplateController: IUpdateWeightsTemplateController;
  IDeleteWeightsTemplateController: IDeleteWeightsTemplateController;

  // Controllers — Minimal Staff Templates
  IListMinimalStaffTemplatesController: IListMinimalStaffTemplatesController;
  IGetMinimalStaffTemplateController: IGetMinimalStaffTemplateController;
  ICreateMinimalStaffTemplateController: ICreateMinimalStaffTemplateController;
  IUpdateMinimalStaffTemplateController: IUpdateMinimalStaffTemplateController;
  IDeleteMinimalStaffTemplateController: IDeleteMinimalStaffTemplateController;

  // Controllers — Global Wishes Templates
  IListGlobalWishesTemplatesController: IListGlobalWishesTemplatesController;
  IGetGlobalWishesTemplateController: IGetGlobalWishesTemplateController;
  ICreateGlobalWishesTemplateController: ICreateGlobalWishesTemplateController;
  IUpdateGlobalWishesTemplateController: IUpdateGlobalWishesTemplateController;
  IDeleteGlobalWishesTemplateController: IDeleteGlobalWishesTemplateController;

  // Controllers — Solver
  ICheckSolverHealthController: ICheckSolverHealthController;
  IExecuteSolverFetchController: IExecuteSolverFetchController;
  IExecuteSolverSolveController: IExecuteSolverSolveController;
  IExecuteSolverSolveMultipleController: IExecuteSolverSolveMultipleController;
  IExecuteSolverInsertController: IExecuteSolverInsertController;
  IExecuteSolverDeleteController: IExecuteSolverDeleteController;
  IImportSolutionController: IImportSolutionController;
  IGetSolverProgressController: IGetSolverProgressController;
  IGetLastInsertedSolutionController: IGetLastInsertedSolutionController;
}
