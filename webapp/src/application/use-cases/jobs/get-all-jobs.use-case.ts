import {SolverJob} from '@/entities/models/solver.model';
import {IJobRepository} from '@/application/ports/job.repository';

export interface IGetAllJobsUseCase {
    (input: { caseId: number; monthYear: string }): Promise<SolverJob[]>;
}

export function makeGetAllJobsUseCase(
    jobRepository: IJobRepository
): IGetAllJobsUseCase {
    return async ({caseId, monthYear}) => {
        return jobRepository.getAll(caseId, monthYear);
    };
}
