import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {LowdbJobRepository} from '@/infrastructure/repositories/lowdb-job.repository';
import {makeGetAllJobsUseCase} from '@/application/use-cases/jobs/get-all-jobs.use-case';
import {makeGetJobUseCase} from '@/application/use-cases/jobs/get-job.use-case';
import {makeCreateJobUseCase} from '@/application/use-cases/jobs/create-job.use-case';
import {makeGetAllJobsController} from '@/controllers/jobs/get-all-jobs.controller';
import {makeGetJobController} from '@/controllers/jobs/get-job.controller';
import {makeCreateJobController} from '@/controllers/jobs/create-job.controller';

export function createJobsModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IJobRepository).toClass(LowdbJobRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IGetAllJobsUseCase).toHigherOrderFunction(makeGetAllJobsUseCase, [DI_SYMBOLS.IJobRepository]);
    m.bind(DI_SYMBOLS.IGetJobUseCase).toHigherOrderFunction(makeGetJobUseCase, [DI_SYMBOLS.IJobRepository]);
    m.bind(DI_SYMBOLS.ICreateJobUseCase).toHigherOrderFunction(makeCreateJobUseCase, [DI_SYMBOLS.IJobRepository]);

    m.bind(DI_SYMBOLS.IGetAllJobsController).toHigherOrderFunction(makeGetAllJobsController, [DI_SYMBOLS.IGetAllJobsUseCase]);
    m.bind(DI_SYMBOLS.IGetJobController).toHigherOrderFunction(makeGetJobController, [DI_SYMBOLS.IGetJobUseCase]);
    m.bind(DI_SYMBOLS.ICreateJobController).toHigherOrderFunction(makeCreateJobController, [DI_SYMBOLS.ICreateJobUseCase]);

    return m;
}
