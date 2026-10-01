import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {IMinimalStaffRepository} from '@/application/ports/minimal-staff.repository';

export interface IGetMinimalStaffUseCase {
    (input: { caseId: number; monthYear: string }): Promise<MinimalStaffRequirements>;
}

export function makeGetMinimalStaffUseCase(
    minimalStaffRepository: IMinimalStaffRepository
): IGetMinimalStaffUseCase {
    return async ({caseId, monthYear}) => {
        return minimalStaffRepository.get(caseId, monthYear);
    };
}
