import {IWishesAndBlockedRepository} from '@/application/ports/wishes-and-blocked.repository';
import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {getWishesAndBlockedDb} from '@/infrastructure/persistence/lowdb/wishes-and-blocked.db';
import {generateMonthlyDataFromWeeklyData} from '@/lib/services/global-to-current-wishes-converter';

export class LowdbWishesAndBlockedRepository implements IWishesAndBlockedRepository {
    async getAll(caseId: number, monthYear: string): Promise<WishesAndBlockedEmployee[]> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        return db.data.employees;
    }

    async getByKey(caseId: number, monthYear: string, key: number): Promise<WishesAndBlockedEmployee | null> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        return db.data.employees.find((e) => e.key === key) ?? null;
    }

    async create(caseId: number, monthYear: string, entry: WishesAndBlockedEmployee): Promise<void> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        db.data.employees.push(entry);
        await db.write();
    }

    async update(caseId: number, monthYear: string, key: number, data: Partial<WishesAndBlockedEmployee>): Promise<void> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        const index = db.data.employees.findIndex((e) => e.key === key);
        if (index !== -1) {
            db.data.employees[index] = {...db.data.employees[index], ...data};
            await db.write();
        }
    }

    async delete(caseId: number, monthYear: string, key: number): Promise<void> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        db.data.employees = db.data.employees.filter((e) => e.key !== key);
        await db.write();
    }

    async deleteAll(caseId: number, monthYear: string): Promise<void> {
        const db = await getWishesAndBlockedDb(caseId, monthYear);
        db.data.employees = [];
        await db.write();
    }

    async generateFromGlobal(caseId: number, monthYear: string, globalEntry: WishesAndBlockedEmployee): Promise<void> {
        const [monthStr, yearStr] = monthYear.split('_');
        const month = parseInt(monthStr, 10);
        const year = parseInt(yearStr, 10);

        const monthlyData = generateMonthlyDataFromWeeklyData(globalEntry, year, month);

        const db = await getWishesAndBlockedDb(caseId, monthYear);
        const index = db.data.employees.findIndex((e) => e.key === globalEntry.key);
        if (index === -1) {
            db.data.employees.push({
                key: globalEntry.key,
                firstname: globalEntry.firstname,
                name: globalEntry.name,
                wish_days: monthlyData.wish_days,
                wish_shifts: monthlyData.wish_shifts,
                work_days: monthlyData.work_days,
                work_shifts: monthlyData.work_shifts,
                blocked_days: monthlyData.blocked_days,
                blocked_shifts: monthlyData.blocked_shifts,
            });
        } else {
            db.data.employees[index] = {
                ...db.data.employees[index],
                wish_days: monthlyData.wish_days,
                wish_shifts: monthlyData.wish_shifts,
                work_days: monthlyData.work_days,
                work_shifts: monthlyData.work_shifts,
                blocked_days: monthlyData.blocked_days,
                blocked_shifts: monthlyData.blocked_shifts,
            };
        }
        await db.write();
    }
}
