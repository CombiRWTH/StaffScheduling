import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';

export interface IMinimalStaffRepository {
    get(caseId: number, monthYear: string): Promise<MinimalStaffRequirements>;

    update(caseId: number, monthYear: string, data: MinimalStaffRequirements): Promise<void>;
}
