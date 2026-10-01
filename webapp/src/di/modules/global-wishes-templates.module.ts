import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {
    makeListGlobalWishesTemplatesUseCase
} from '@/application/use-cases/templates/global-wishes/list-global-wishes-templates.use-case';
import {
    makeGetGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/get-global-wishes-template.use-case';
import {
    makeCreateGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/create-global-wishes-template.use-case';
import {
    makeUpdateGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/update-global-wishes-template.use-case';
import {
    makeDeleteGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/delete-global-wishes-template.use-case';
import {
    makeListGlobalWishesTemplatesController
} from '@/controllers/templates/global-wishes/list-global-wishes-templates.controller';
import {
    makeGetGlobalWishesTemplateController
} from '@/controllers/templates/global-wishes/get-global-wishes-template.controller';
import {
    makeCreateGlobalWishesTemplateController
} from '@/controllers/templates/global-wishes/create-global-wishes-template.controller';
import {
    makeUpdateGlobalWishesTemplateController
} from '@/controllers/templates/global-wishes/update-global-wishes-template.controller';
import {
    makeDeleteGlobalWishesTemplateController
} from '@/controllers/templates/global-wishes/delete-global-wishes-template.controller';

export function createGlobalWishesTemplatesModule() {
    const m = createModule();

    // IGlobalWishesTemplateRepository is already registered in global-wishes.module.ts (used by import use-case).
    // This module reuses that binding for all template CRUD use-cases.

    m.bind(DI_SYMBOLS.IListGlobalWishesTemplatesUseCase).toHigherOrderFunction(makeListGlobalWishesTemplatesUseCase, [DI_SYMBOLS.IGlobalWishesTemplateRepository]);
    m.bind(DI_SYMBOLS.IGetGlobalWishesTemplateUseCase).toHigherOrderFunction(makeGetGlobalWishesTemplateUseCase, [DI_SYMBOLS.IGlobalWishesTemplateRepository]);
    m.bind(DI_SYMBOLS.ICreateGlobalWishesTemplateUseCase).toHigherOrderFunction(makeCreateGlobalWishesTemplateUseCase, [DI_SYMBOLS.IGlobalWishesTemplateRepository]);
    m.bind(DI_SYMBOLS.IUpdateGlobalWishesTemplateUseCase).toHigherOrderFunction(makeUpdateGlobalWishesTemplateUseCase, [DI_SYMBOLS.IGlobalWishesTemplateRepository]);
    m.bind(DI_SYMBOLS.IDeleteGlobalWishesTemplateUseCase).toHigherOrderFunction(makeDeleteGlobalWishesTemplateUseCase, [DI_SYMBOLS.IGlobalWishesTemplateRepository]);

    m.bind(DI_SYMBOLS.IListGlobalWishesTemplatesController).toHigherOrderFunction(makeListGlobalWishesTemplatesController, [DI_SYMBOLS.IListGlobalWishesTemplatesUseCase]);
    m.bind(DI_SYMBOLS.IGetGlobalWishesTemplateController).toHigherOrderFunction(makeGetGlobalWishesTemplateController, [DI_SYMBOLS.IGetGlobalWishesTemplateUseCase]);
    m.bind(DI_SYMBOLS.ICreateGlobalWishesTemplateController).toHigherOrderFunction(makeCreateGlobalWishesTemplateController, [DI_SYMBOLS.ICreateGlobalWishesTemplateUseCase]);
    m.bind(DI_SYMBOLS.IUpdateGlobalWishesTemplateController).toHigherOrderFunction(makeUpdateGlobalWishesTemplateController, [DI_SYMBOLS.IUpdateGlobalWishesTemplateUseCase]);
    m.bind(DI_SYMBOLS.IDeleteGlobalWishesTemplateController).toHigherOrderFunction(makeDeleteGlobalWishesTemplateController, [DI_SYMBOLS.IDeleteGlobalWishesTemplateUseCase]);

    return m;
}
