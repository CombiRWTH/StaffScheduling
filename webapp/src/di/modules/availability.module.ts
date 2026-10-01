import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {makeCreateAvailabilityUseCase} from '@/application/use-cases/availability/create-availability.use-case';
import {makeDeleteAvailabilityUseCase} from '@/application/use-cases/availability/delete-availability.use-case';
import {makeGetAllAvailabilityUseCase} from '@/application/use-cases/availability/get-all-availability.use-case';
import {makeGetAvailabilityByKeyUseCase} from '@/application/use-cases/availability/get-availability-by-key.use-case';
import {makeUpdateAvailabilityUseCase} from '@/application/use-cases/availability/update-availability.use-case';
import {makeCreateAvailabilityController} from '@/controllers/availability/create-availability.controller';
import {makeDeleteAvailabilityController} from '@/controllers/availability/delete-availability.controller';
import {makeGetAllAvailabilityController} from '@/controllers/availability/get-all-availability.controller';
import {makeGetAvailabilityByKeyController} from '@/controllers/availability/get-availability-by-key.controller';
import {makeUpdateAvailabilityController} from '@/controllers/availability/update-availability.controller';
import {LowdbAvailabilityRepository} from '@/infrastructure/repositories/lowdb-availability.repository';

export function createAvailabilityModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IAvailabilityRepository).toClass(LowdbAvailabilityRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IGetAllAvailabilityUseCase).toHigherOrderFunction(makeGetAllAvailabilityUseCase, [DI_SYMBOLS.IAvailabilityRepository]);
    m.bind(DI_SYMBOLS.IGetAvailabilityByKeyUseCase).toHigherOrderFunction(makeGetAvailabilityByKeyUseCase, [DI_SYMBOLS.IAvailabilityRepository]);
    m.bind(DI_SYMBOLS.ICreateAvailabilityUseCase).toHigherOrderFunction(makeCreateAvailabilityUseCase, [DI_SYMBOLS.IAvailabilityRepository]);
    m.bind(DI_SYMBOLS.IUpdateAvailabilityUseCase).toHigherOrderFunction(makeUpdateAvailabilityUseCase, [DI_SYMBOLS.IAvailabilityRepository]);
    m.bind(DI_SYMBOLS.IDeleteAvailabilityUseCase).toHigherOrderFunction(makeDeleteAvailabilityUseCase, [DI_SYMBOLS.IAvailabilityRepository]);

    m.bind(DI_SYMBOLS.IGetAllAvailabilityController).toHigherOrderFunction(makeGetAllAvailabilityController, [DI_SYMBOLS.IGetAllAvailabilityUseCase]);
    m.bind(DI_SYMBOLS.IGetAvailabilityByKeyController).toHigherOrderFunction(makeGetAvailabilityByKeyController, [DI_SYMBOLS.IGetAvailabilityByKeyUseCase]);
    m.bind(DI_SYMBOLS.ICreateAvailabilityController).toHigherOrderFunction(makeCreateAvailabilityController, [DI_SYMBOLS.ICreateAvailabilityUseCase]);
    m.bind(DI_SYMBOLS.IUpdateAvailabilityController).toHigherOrderFunction(makeUpdateAvailabilityController, [DI_SYMBOLS.IUpdateAvailabilityUseCase]);
    m.bind(DI_SYMBOLS.IDeleteAvailabilityController).toHigherOrderFunction(makeDeleteAvailabilityController, [DI_SYMBOLS.IDeleteAvailabilityUseCase]);

    return m;
}
