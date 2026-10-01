import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {LowdbCaseRepository} from '@/infrastructure/repositories/lowdb-case.repository';
import {makeListCasesUseCase} from '@/application/use-cases/cases/list-cases.use-case';
import {makeListCasesController} from '@/controllers/cases/list-cases.controller';

export function createCasesModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.ICaseRepository).toClass(LowdbCaseRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IListCasesUseCase).toHigherOrderFunction(makeListCasesUseCase, [DI_SYMBOLS.ICaseRepository]);

    m.bind(DI_SYMBOLS.IListCasesController).toHigherOrderFunction(makeListCasesController, [DI_SYMBOLS.IListCasesUseCase]);

    return m;
}
