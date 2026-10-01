import { IGlobalAvailabilityRepository } from "@/application/ports/global-availability.repository";
import { AvailabilityEmployee } from "@/entities/models/availability.model";
import { getGlobalAvailabilityDb } from "@/infrastructure/persistence/lowdb/global-availability.db";

export class LowdbGlobalAvailabilityRepository implements IGlobalAvailabilityRepository {
  async getAll(caseId: number, monthYear: string): Promise<AvailabilityEmployee[]> {
    const db = await getGlobalAvailabilityDb(caseId, monthYear);
    return db.data.employees;
  }

  async getByKey(caseId: number, monthYear: string, key: number): Promise<AvailabilityEmployee | null> {
    const db = await getGlobalAvailabilityDb(caseId, monthYear);
    return db.data.employees.find((e) => e.key === key) ?? null;
  }

  async create(caseId: number, monthYear: string, entry: AvailabilityEmployee): Promise<void> {
    const db = await getGlobalAvailabilityDb(caseId, monthYear);
    db.data.employees.push(entry);
    await db.write();
  }

  async update(caseId: number, monthYear: string, key: number, data: Partial<AvailabilityEmployee>): Promise<void> {
    const db = await getGlobalAvailabilityDb(caseId, monthYear);
    const index = db.data.employees.findIndex((e) => e.key === key);
    if (index !== -1) {
      db.data.employees[index] = { ...db.data.employees[index], ...data };
      await db.write();
    }
  }

  async delete(caseId: number, monthYear: string, key: number): Promise<void> {
    const db = await getGlobalAvailabilityDb(caseId, monthYear);
    db.data.employees = db.data.employees.filter((e) => e.key !== key);
    await db.write();
  }
}
