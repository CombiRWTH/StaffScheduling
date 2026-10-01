import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {LowdbMinimalStaffRepository} from '@/infrastructure/repositories/lowdb-minimal-staff.repository';
import {makeGetMinimalStaffUseCase} from '@/application/use-cases/minimal-staff/get-minimal-staff.use-case';
import {makeUpdateMinimalStaffUseCase} from '@/application/use-cases/minimal-staff/update-minimal-staff.use-case';
import {makeGetMinimalStaffController} from '@/controllers/minimal-staff/get-minimal-staff.controller';
import {makeUpdateMinimalStaffController} from '@/controllers/minimal-staff/update-minimal-staff.controller';

export function createMinimalStaffModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IMinimalStaffRepository).toClass(LowdbMinimalStaffRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IGetMinimalStaffUseCase).toHigherOrderFunction(makeGetMinimalStaffUseCase, [DI_SYMBOLS.IMinimalStaffRepository]);
    m.bind(DI_SYMBOLS.IUpdateMinimalStaffUseCase).toHigherOrderFunction(makeUpdateMinimalStaffUseCase, [DI_SYMBOLS.IMinimalStaffRepository]);

    m.bind(DI_SYMBOLS.IGetMinimalStaffController).toHigherOrderFunction(makeGetMinimalStaffController, [DI_SYMBOLS.IGetMinimalStaffUseCase]);
    m.bind(DI_SYMBOLS.IUpdateMinimalStaffController).toHigherOrderFunction(makeUpdateMinimalStaffController, [DI_SYMBOLS.IUpdateMinimalStaffUseCase]);

    return m;
}
