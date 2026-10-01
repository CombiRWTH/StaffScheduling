import 'server-only';
import {createContainer} from '@evyweb/ioctopus';
import {DI_RETURN_TYPES, DI_SYMBOLS} from '@/di/types';
import {createEmployeesModule} from '@/di/modules/employees.module';
import {createWeightsModule} from '@/di/modules/weights.module';
import {createMinimalStaffModule} from '@/di/modules/minimal-staff.module';
import {createWishesAndBlockedModule} from '@/di/modules/wishes-and-blocked.module';
import {createGlobalWishesModule} from '@/di/modules/global-wishes.module';
import {createSchedulesModule} from '@/di/modules/schedules.module';
import {createJobsModule} from '@/di/modules/jobs.module';
import {createCasesModule} from '@/di/modules/cases.module';
import {createSolverModule} from '@/di/modules/solver.module';
import {createWeightsTemplatesModule} from '@/di/modules/weights-templates.module';
import {createMinimalStaffTemplatesModule} from '@/di/modules/minimal-staff-templates.module';
import {createGlobalWishesTemplatesModule} from '@/di/modules/global-wishes-templates.module';
import {createAvailabilityModule} from '@/di/modules/availability.module';
import {createGlobalAvailabilityModule} from '@/di/modules/global-availability.module';

const ApplicationContainer = createContainer();

ApplicationContainer.load(Symbol('EmployeesModule'), createEmployeesModule());
ApplicationContainer.load(Symbol('WeightsModule'), createWeightsModule());
ApplicationContainer.load(Symbol('MinimalStaffModule'), createMinimalStaffModule());
ApplicationContainer.load(Symbol('WishesAndBlockedModule'), createWishesAndBlockedModule());
ApplicationContainer.load(Symbol('GlobalWishesModule'), createGlobalWishesModule());
ApplicationContainer.load(Symbol('AvailabilityModule'), createAvailabilityModule());
ApplicationContainer.load(Symbol('GlobalAvailabilityModule'), createGlobalAvailabilityModule());
ApplicationContainer.load(Symbol('SchedulesModule'), createSchedulesModule());
ApplicationContainer.load(Symbol('JobsModule'), createJobsModule());
ApplicationContainer.load(Symbol('CasesModule'), createCasesModule());
ApplicationContainer.load(Symbol('SolverModule'), createSolverModule());
ApplicationContainer.load(Symbol('WeightsTemplatesModule'), createWeightsTemplatesModule());
ApplicationContainer.load(Symbol('MinimalStaffTemplatesModule'), createMinimalStaffTemplatesModule());
ApplicationContainer.load(Symbol('GlobalWishesTemplatesModule'), createGlobalWishesTemplatesModule());

export function getInjection<K extends keyof typeof DI_SYMBOLS>(
    symbol: K
): DI_RETURN_TYPES[K] {
    return ApplicationContainer.get(DI_SYMBOLS[symbol]);
}
