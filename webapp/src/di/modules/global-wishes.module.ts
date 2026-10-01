import { createModule } from "@evyweb/ioctopus";
import { DI_SYMBOLS } from "@/di/types";
import { LowdbGlobalWishesAndBlockedRepository } from "@/infrastructure/repositories/lowdb-global-wishes-and-blocked.repository";
import { GlobalWishesTemplateRepositoryAdapter } from "@/infrastructure/repositories/global-wishes-template.repository";
import { makeGetAllGlobalWishesUseCase } from "@/application/use-cases/global-wishes/get-all-global-wishes.use-case";
import { makeGetGlobalWishesByKeyUseCase } from "@/application/use-cases/global-wishes/get-global-wishes-by-key.use-case";
import { makeCreateGlobalWishesUseCase } from "@/application/use-cases/global-wishes/create-global-wishes.use-case";
import { makeUpdateGlobalWishesUseCase } from "@/application/use-cases/global-wishes/update-global-wishes.use-case";
import { makeDeleteGlobalWishesUseCase } from "@/application/use-cases/global-wishes/delete-global-wishes.use-case";
import { makeImportGlobalWishesTemplateUseCase } from "@/application/use-cases/global-wishes/import-global-wishes-template.use-case";
import { makeGetAllGlobalWishesController } from "@/controllers/global-wishes/get-all-global-wishes.controller";
import { makeGetGlobalWishesByKeyController } from "@/controllers/global-wishes/get-global-wishes-by-key.controller";
import { makeCreateGlobalWishesController } from "@/controllers/global-wishes/create-global-wishes.controller";
import { makeUpdateGlobalWishesController } from "@/controllers/global-wishes/update-global-wishes.controller";
import { makeDeleteGlobalWishesController } from "@/controllers/global-wishes/delete-global-wishes.controller";
import { makeImportGlobalWishesTemplateController } from "@/controllers/global-wishes/import-global-wishes-template.controller";

export function createGlobalWishesModule() {
  const m = createModule();

  m.bind(DI_SYMBOLS.IGlobalWishesAndBlockedRepository).toClass(LowdbGlobalWishesAndBlockedRepository, [], "singleton");
  m.bind(DI_SYMBOLS.IGlobalWishesTemplateRepository).toClass(GlobalWishesTemplateRepositoryAdapter, [], "singleton");

  m.bind(DI_SYMBOLS.IGetAllGlobalWishesUseCase).toHigherOrderFunction(makeGetAllGlobalWishesUseCase, [
    DI_SYMBOLS.IGlobalWishesAndBlockedRepository,
  ]);
  m.bind(DI_SYMBOLS.IGetGlobalWishesByKeyUseCase).toHigherOrderFunction(makeGetGlobalWishesByKeyUseCase, [
    DI_SYMBOLS.IGlobalWishesAndBlockedRepository,
  ]);
  m.bind(DI_SYMBOLS.ICreateGlobalWishesUseCase).toHigherOrderFunction(makeCreateGlobalWishesUseCase, [
    DI_SYMBOLS.IGlobalWishesAndBlockedRepository,
    DI_SYMBOLS.IWishesAndBlockedRepository,
  ]);
  m.bind(DI_SYMBOLS.IUpdateGlobalWishesUseCase).toHigherOrderFunction(makeUpdateGlobalWishesUseCase, [
    DI_SYMBOLS.IGlobalWishesAndBlockedRepository,
    DI_SYMBOLS.IWishesAndBlockedRepository,
  ]);
  m.bind(DI_SYMBOLS.IDeleteGlobalWishesUseCase).toHigherOrderFunction(makeDeleteGlobalWishesUseCase, [
    DI_SYMBOLS.IGlobalWishesAndBlockedRepository,
    DI_SYMBOLS.IWishesAndBlockedRepository,
  ]);
  m.bind(DI_SYMBOLS.IImportGlobalWishesTemplateUseCase).toHigherOrderFunction(
    makeImportGlobalWishesTemplateUseCase,
    [],
  );

  m.bind(DI_SYMBOLS.IGetAllGlobalWishesController).toHigherOrderFunction(makeGetAllGlobalWishesController, [
    DI_SYMBOLS.IGetAllGlobalWishesUseCase,
  ]);
  m.bind(DI_SYMBOLS.IGetGlobalWishesByKeyController).toHigherOrderFunction(makeGetGlobalWishesByKeyController, [
    DI_SYMBOLS.IGetGlobalWishesByKeyUseCase,
  ]);
  m.bind(DI_SYMBOLS.ICreateGlobalWishesController).toHigherOrderFunction(makeCreateGlobalWishesController, [
    DI_SYMBOLS.ICreateGlobalWishesUseCase,
  ]);
  m.bind(DI_SYMBOLS.IUpdateGlobalWishesController).toHigherOrderFunction(makeUpdateGlobalWishesController, [
    DI_SYMBOLS.IUpdateGlobalWishesUseCase,
  ]);
  m.bind(DI_SYMBOLS.IDeleteGlobalWishesController).toHigherOrderFunction(makeDeleteGlobalWishesController, [
    DI_SYMBOLS.IDeleteGlobalWishesUseCase,
  ]);
  m.bind(DI_SYMBOLS.IImportGlobalWishesTemplateController).toHigherOrderFunction(
    makeImportGlobalWishesTemplateController,
    [DI_SYMBOLS.IImportGlobalWishesTemplateUseCase],
  );

  return m;
}
