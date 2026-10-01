import { createModule } from "@evyweb/ioctopus";
import { DI_SYMBOLS } from "@/di/types";
import { makeCreateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/create-global-availability.use-case";
import { makeDeleteGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/delete-global-availability.use-case";
import { makeGetAllGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/get-all-global-availability.use-case";
import { makeGetGlobalAvailabilityByKeyUseCase } from "@/application/use-cases/global-availability/get-global-availability-by-key.use-case";
import { makeUpdateGlobalAvailabilityUseCase } from "@/application/use-cases/global-availability/update-global-availability.use-case";
import { makeCreateGlobalAvailabilityController } from "@/controllers/global-availability/create-global-availability.controller";
import { makeDeleteGlobalAvailabilityController } from "@/controllers/global-availability/delete-global-availability.controller";
import { makeGetAllGlobalAvailabilityController } from "@/controllers/global-availability/get-all-global-availability.controller";
import { makeGetGlobalAvailabilityByKeyController } from "@/controllers/global-availability/get-global-availability-by-key.controller";
import { makeUpdateGlobalAvailabilityController } from "@/controllers/global-availability/update-global-availability.controller";
import { LowdbGlobalAvailabilityRepository } from "@/infrastructure/repositories/lowdb-global-availability.repository";

export function createGlobalAvailabilityModule() {
  const m = createModule();

  m.bind(DI_SYMBOLS.IGlobalAvailabilityRepository).toClass(LowdbGlobalAvailabilityRepository, [], "singleton");

  m.bind(DI_SYMBOLS.IGetAllGlobalAvailabilityUseCase).toHigherOrderFunction(makeGetAllGlobalAvailabilityUseCase, [
    DI_SYMBOLS.IGlobalAvailabilityRepository,
  ]);
  m.bind(DI_SYMBOLS.IGetGlobalAvailabilityByKeyUseCase).toHigherOrderFunction(makeGetGlobalAvailabilityByKeyUseCase, [
    DI_SYMBOLS.IGlobalAvailabilityRepository,
  ]);
  m.bind(DI_SYMBOLS.ICreateGlobalAvailabilityUseCase).toHigherOrderFunction(makeCreateGlobalAvailabilityUseCase, [
    DI_SYMBOLS.IGlobalAvailabilityRepository,
    DI_SYMBOLS.IAvailabilityRepository,
  ]);
  m.bind(DI_SYMBOLS.IUpdateGlobalAvailabilityUseCase).toHigherOrderFunction(makeUpdateGlobalAvailabilityUseCase, [
    DI_SYMBOLS.IGlobalAvailabilityRepository,
    DI_SYMBOLS.IAvailabilityRepository,
  ]);
  m.bind(DI_SYMBOLS.IDeleteGlobalAvailabilityUseCase).toHigherOrderFunction(makeDeleteGlobalAvailabilityUseCase, [
    DI_SYMBOLS.IGlobalAvailabilityRepository,
    DI_SYMBOLS.IAvailabilityRepository,
  ]);

  m.bind(DI_SYMBOLS.IGetAllGlobalAvailabilityController).toHigherOrderFunction(makeGetAllGlobalAvailabilityController, [
    DI_SYMBOLS.IGetAllGlobalAvailabilityUseCase,
  ]);
  m.bind(DI_SYMBOLS.IGetGlobalAvailabilityByKeyController).toHigherOrderFunction(
    makeGetGlobalAvailabilityByKeyController,
    [DI_SYMBOLS.IGetGlobalAvailabilityByKeyUseCase],
  );
  m.bind(DI_SYMBOLS.ICreateGlobalAvailabilityController).toHigherOrderFunction(makeCreateGlobalAvailabilityController, [
    DI_SYMBOLS.ICreateGlobalAvailabilityUseCase,
  ]);
  m.bind(DI_SYMBOLS.IUpdateGlobalAvailabilityController).toHigherOrderFunction(makeUpdateGlobalAvailabilityController, [
    DI_SYMBOLS.IUpdateGlobalAvailabilityUseCase,
  ]);
  m.bind(DI_SYMBOLS.IDeleteGlobalAvailabilityController).toHigherOrderFunction(makeDeleteGlobalAvailabilityController, [
    DI_SYMBOLS.IDeleteGlobalAvailabilityUseCase,
  ]);

  return m;
}
