import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {LowdbWeightsRepository} from '@/infrastructure/repositories/lowdb-weights.repository';
import {makeGetWeightsUseCase} from '@/application/use-cases/weights/get-weights.use-case';
import {makeUpdateWeightsUseCase} from '@/application/use-cases/weights/update-weights.use-case';
import {makeGetWeightsController} from '@/controllers/weights/get-weights.controller';
import {makeUpdateWeightsController} from '@/controllers/weights/update-weights.controller';

export function createWeightsModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IWeightsRepository).toClass(LowdbWeightsRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IGetWeightsUseCase).toHigherOrderFunction(makeGetWeightsUseCase, [DI_SYMBOLS.IWeightsRepository]);
    m.bind(DI_SYMBOLS.IUpdateWeightsUseCase).toHigherOrderFunction(makeUpdateWeightsUseCase, [DI_SYMBOLS.IWeightsRepository]);

    m.bind(DI_SYMBOLS.IGetWeightsController).toHigherOrderFunction(makeGetWeightsController, [DI_SYMBOLS.IGetWeightsUseCase]);
    m.bind(DI_SYMBOLS.IUpdateWeightsController).toHigherOrderFunction(makeUpdateWeightsController, [DI_SYMBOLS.IUpdateWeightsUseCase]);

    return m;
}
