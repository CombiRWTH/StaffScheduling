import {IMinimalStaffRepository} from '@/application/ports/minimal-staff.repository';
import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {getMinimalStaffDb} from '@/infrastructure/persistence/lowdb/minimal-staff.db';

export class LowdbMinimalStaffRepository implements IMinimalStaffRepository {
    async get(caseId: number, monthYear: string): Promise<MinimalStaffRequirements> {
        const db = await getMinimalStaffDb(caseId, monthYear);
        return db.data;
    }

    async update(caseId: number, monthYear: string, data: MinimalStaffRequirements): Promise<void> {
        const db = await getMinimalStaffDb(caseId, monthYear);
        db.data = data;
        await db.write();
    }
}
