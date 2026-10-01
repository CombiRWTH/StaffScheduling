import { createModule } from "@evyweb/ioctopus";
import { DI_SYMBOLS } from "@/di/types";
import { LowdbWeightsTemplateRepository } from "@/infrastructure/repositories/lowdb-weights-template.repository";
import { makeListWeightsTemplatesUseCase } from "@/application/use-cases/templates/weights/list-weights-templates.use-case";
import { makeGetWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/get-weights-template.use-case";
import { makeCreateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/create-weights-template.use-case";
import { makeUpdateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/update-weights-template.use-case";
import { makeDeleteWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/delete-weights-template.use-case";
import { makeListWeightsTemplatesController } from "@/controllers/templates/weights/list-weights-templates.controller";
import { makeGetWeightsTemplateController } from "@/controllers/templates/weights/get-weights-template.controller";
import { makeCreateWeightsTemplateController } from "@/controllers/templates/weights/create-weights-template.controller";
import { makeUpdateWeightsTemplateController } from "@/controllers/templates/weights/update-weights-template.controller";
import { makeDeleteWeightsTemplateController } from "@/controllers/templates/weights/delete-weights-template.controller";

export function createWeightsTemplatesModule() {
  const m = createModule();

  m.bind(DI_SYMBOLS.IWeightsTemplateRepository).toClass(LowdbWeightsTemplateRepository, [], "singleton");

  m.bind(DI_SYMBOLS.IListWeightsTemplatesUseCase).toHigherOrderFunction(makeListWeightsTemplatesUseCase, [
    DI_SYMBOLS.IWeightsTemplateRepository,
  ]);
  m.bind(DI_SYMBOLS.IGetWeightsTemplateUseCase).toHigherOrderFunction(makeGetWeightsTemplateUseCase, [
    DI_SYMBOLS.IWeightsTemplateRepository,
  ]);
  m.bind(DI_SYMBOLS.ICreateWeightsTemplateUseCase).toHigherOrderFunction(makeCreateWeightsTemplateUseCase, [
    DI_SYMBOLS.IWeightsTemplateRepository,
  ]);
  m.bind(DI_SYMBOLS.IUpdateWeightsTemplateUseCase).toHigherOrderFunction(makeUpdateWeightsTemplateUseCase, [
    DI_SYMBOLS.IWeightsTemplateRepository,
  ]);
  m.bind(DI_SYMBOLS.IDeleteWeightsTemplateUseCase).toHigherOrderFunction(makeDeleteWeightsTemplateUseCase, [
    DI_SYMBOLS.IWeightsTemplateRepository,
  ]);

  m.bind(DI_SYMBOLS.IListWeightsTemplatesController).toHigherOrderFunction(makeListWeightsTemplatesController, [
    DI_SYMBOLS.IListWeightsTemplatesUseCase,
  ]);
  m.bind(DI_SYMBOLS.IGetWeightsTemplateController).toHigherOrderFunction(makeGetWeightsTemplateController, [
    DI_SYMBOLS.IGetWeightsTemplateUseCase,
  ]);
  m.bind(DI_SYMBOLS.ICreateWeightsTemplateController).toHigherOrderFunction(makeCreateWeightsTemplateController, [
    DI_SYMBOLS.ICreateWeightsTemplateUseCase,
  ]);
  m.bind(DI_SYMBOLS.IUpdateWeightsTemplateController).toHigherOrderFunction(makeUpdateWeightsTemplateController, [
    DI_SYMBOLS.IUpdateWeightsTemplateUseCase,
  ]);
  m.bind(DI_SYMBOLS.IDeleteWeightsTemplateController).toHigherOrderFunction(makeDeleteWeightsTemplateController, [
    DI_SYMBOLS.IDeleteWeightsTemplateUseCase,
  ]);

  return m;
}
