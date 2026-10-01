import {generateMonthlyAvailabilityFromWeeklyData} from '@/lib/services/global-to-current-wishes-converter';
import {IAvailabilityRepository} from '@/application/ports/availability.repository';
import {AvailabilityEmployee} from '@/entities/models/availability.model';
import {getAvailabilityDb} from '@/infrastructure/persistence/lowdb/availability.db';

export class LowdbAvailabilityRepository implements IAvailabilityRepository {
    async getAll(caseId: number, monthYear: string): Promise<AvailabilityEmployee[]> {
        const db = await getAvailabilityDb(caseId, monthYear);
        return db.data.employees;
    }

    async getByKey(caseId: number, monthYear: string, key: number): Promise<AvailabilityEmployee | null> {
        const db = await getAvailabilityDb(caseId, monthYear);
        return db.data.employees.find((e) => e.key === key) ?? null;
    }

    async create(caseId: number, monthYear: string, entry: AvailabilityEmployee): Promise<void> {
        const db = await getAvailabilityDb(caseId, monthYear);
        db.data.employees.push(entry);
        await db.write();
    }

    async update(caseId: number, monthYear: string, key: number, data: Partial<AvailabilityEmployee>): Promise<void> {
        const db = await getAvailabilityDb(caseId, monthYear);
        const index = db.data.employees.findIndex((e) => e.key === key);
        if (index !== -1) {
            db.data.employees[index] = {...db.data.employees[index], ...data};
            await db.write();
        }
    }

    async delete(caseId: number, monthYear: string, key: number): Promise<void> {
        const db = await getAvailabilityDb(caseId, monthYear);
        db.data.employees = db.data.employees.filter((e) => e.key !== key);
        await db.write();
    }

    async deleteAll(caseId: number, monthYear: string): Promise<void> {
        const db = await getAvailabilityDb(caseId, monthYear);
        db.data.employees = [];
        await db.write();
    }

    async generateFromGlobal(caseId: number, monthYear: string, globalEntry: AvailabilityEmployee): Promise<void> {
        const [monthStr, yearStr] = monthYear.split('_');
        const month = parseInt(monthStr, 10);
        const year = parseInt(yearStr, 10);
        const monthlyData = generateMonthlyAvailabilityFromWeeklyData(globalEntry, year, month);

        const db = await getAvailabilityDb(caseId, monthYear);
        const index = db.data.employees.findIndex((e) => e.key === globalEntry.key);
        if (index === -1) {
            db.data.employees.push({
                key: globalEntry.key,
                firstname: globalEntry.firstname,
                name: globalEntry.name,
                unavailability_days: monthlyData.unavailability_days,
                unavailability_shifts: monthlyData.unavailability_shifts,
            });
        } else {
            db.data.employees[index] = {
                ...db.data.employees[index],
                unavailability_days: monthlyData.unavailability_days,
                unavailability_shifts: monthlyData.unavailability_shifts,
            };
        }
        await db.write();
    }
}
