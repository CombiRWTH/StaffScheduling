import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {
    LowdbMinimalStaffTemplateRepository
} from '@/infrastructure/repositories/lowdb-minimal-staff-template.repository';
import {
    makeListMinimalStaffTemplatesUseCase
} from '@/application/use-cases/templates/minimal-staff/list-minimal-staff-templates.use-case';
import {
    makeGetMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/get-minimal-staff-template.use-case';
import {
    makeCreateMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/create-minimal-staff-template.use-case';
import {
    makeUpdateMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/update-minimal-staff-template.use-case';
import {
    makeDeleteMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/delete-minimal-staff-template.use-case';
import {
    makeListMinimalStaffTemplatesController
} from '@/controllers/templates/minimal-staff/list-minimal-staff-templates.controller';
import {
    makeGetMinimalStaffTemplateController
} from '@/controllers/templates/minimal-staff/get-minimal-staff-template.controller';
import {
    makeCreateMinimalStaffTemplateController
} from '@/controllers/templates/minimal-staff/create-minimal-staff-template.controller';
import {
    makeUpdateMinimalStaffTemplateController
} from '@/controllers/templates/minimal-staff/update-minimal-staff-template.controller';
import {
    makeDeleteMinimalStaffTemplateController
} from '@/controllers/templates/minimal-staff/delete-minimal-staff-template.controller';

export function createMinimalStaffTemplatesModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IMinimalStaffTemplateRepository).toClass(LowdbMinimalStaffTemplateRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IListMinimalStaffTemplatesUseCase).toHigherOrderFunction(makeListMinimalStaffTemplatesUseCase, [DI_SYMBOLS.IMinimalStaffTemplateRepository]);
    m.bind(DI_SYMBOLS.IGetMinimalStaffTemplateUseCase).toHigherOrderFunction(makeGetMinimalStaffTemplateUseCase, [DI_SYMBOLS.IMinimalStaffTemplateRepository]);
    m.bind(DI_SYMBOLS.ICreateMinimalStaffTemplateUseCase).toHigherOrderFunction(makeCreateMinimalStaffTemplateUseCase, [DI_SYMBOLS.IMinimalStaffTemplateRepository]);
    m.bind(DI_SYMBOLS.IUpdateMinimalStaffTemplateUseCase).toHigherOrderFunction(makeUpdateMinimalStaffTemplateUseCase, [DI_SYMBOLS.IMinimalStaffTemplateRepository]);
    m.bind(DI_SYMBOLS.IDeleteMinimalStaffTemplateUseCase).toHigherOrderFunction(makeDeleteMinimalStaffTemplateUseCase, [DI_SYMBOLS.IMinimalStaffTemplateRepository]);

    m.bind(DI_SYMBOLS.IListMinimalStaffTemplatesController).toHigherOrderFunction(makeListMinimalStaffTemplatesController, [DI_SYMBOLS.IListMinimalStaffTemplatesUseCase]);
    m.bind(DI_SYMBOLS.IGetMinimalStaffTemplateController).toHigherOrderFunction(makeGetMinimalStaffTemplateController, [DI_SYMBOLS.IGetMinimalStaffTemplateUseCase]);
    m.bind(DI_SYMBOLS.ICreateMinimalStaffTemplateController).toHigherOrderFunction(makeCreateMinimalStaffTemplateController, [DI_SYMBOLS.ICreateMinimalStaffTemplateUseCase]);
    m.bind(DI_SYMBOLS.IUpdateMinimalStaffTemplateController).toHigherOrderFunction(makeUpdateMinimalStaffTemplateController, [DI_SYMBOLS.IUpdateMinimalStaffTemplateUseCase]);
    m.bind(DI_SYMBOLS.IDeleteMinimalStaffTemplateController).toHigherOrderFunction(makeDeleteMinimalStaffTemplateController, [DI_SYMBOLS.IDeleteMinimalStaffTemplateUseCase]);

    return m;
}
