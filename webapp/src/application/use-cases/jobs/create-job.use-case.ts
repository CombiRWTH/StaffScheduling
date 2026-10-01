import {SolverJob} from '@/entities/models/solver.model';
import {IJobRepository} from '@/application/ports/job.repository';

export interface ICreateJobUseCase {
    (input: { caseId: number; monthYear: string; job: SolverJob }): Promise<void>;
}

export function makeCreateJobUseCase(
    jobRepository: IJobRepository
): ICreateJobUseCase {
    return async ({caseId, monthYear, job}) => {
        await jobRepository.create(caseId, monthYear, job);
        await jobRepository.cleanup(caseId, monthYear);
    };
}
