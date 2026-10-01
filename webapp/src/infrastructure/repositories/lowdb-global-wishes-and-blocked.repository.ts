import { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";
import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { getGlobalWishesAndBlockedDb } from "@/infrastructure/persistence/lowdb/global-wishes-and-blocked.db";

export class LowdbGlobalWishesAndBlockedRepository implements IGlobalWishesAndBlockedRepository {
  async getAll(caseId: number, monthYear: string): Promise<WishesAndBlockedEmployee[]> {
    const db = await getGlobalWishesAndBlockedDb(caseId, monthYear);
    return db.data.employees;
  }

  async getByKey(caseId: number, monthYear: string, key: number): Promise<WishesAndBlockedEmployee | null> {
    const db = await getGlobalWishesAndBlockedDb(caseId, monthYear);
    return db.data.employees.find((e) => e.key === key) ?? null;
  }

  async create(caseId: number, monthYear: string, entry: WishesAndBlockedEmployee): Promise<void> {
    const db = await getGlobalWishesAndBlockedDb(caseId, monthYear);
    db.data.employees.push(entry);
    await db.write();
  }

  async update(caseId: number, monthYear: string, key: number, data: Partial<WishesAndBlockedEmployee>): Promise<void> {
    const db = await getGlobalWishesAndBlockedDb(caseId, monthYear);
    const index = db.data.employees.findIndex((e) => e.key === key);
    if (index !== -1) {
      db.data.employees[index] = { ...db.data.employees[index], ...data };
      await db.write();
    }
  }

  async delete(caseId: number, monthYear: string, key: number): Promise<void> {
    const db = await getGlobalWishesAndBlockedDb(caseId, monthYear);
    db.data.employees = db.data.employees.filter((e) => e.key !== key);
    await db.write();
  }
}
