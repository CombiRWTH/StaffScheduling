import {CaseUnit} from '@/entities/models/case.model';
import {ICaseRepository} from '@/application/ports/case.repository';

export interface IListCasesUseCase {
    (): Promise<CaseUnit[]>;
}

export function makeListCasesUseCase(
    caseRepository: ICaseRepository
): IListCasesUseCase {
    return async () => {
        return caseRepository.list();
    };
}
