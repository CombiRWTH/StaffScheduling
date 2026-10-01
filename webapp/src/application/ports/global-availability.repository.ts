import { AvailabilityEmployee } from "@/entities/models/availability.model";

export interface IGlobalAvailabilityRepository {
  getAll(caseId: number, monthYear: string): Promise<AvailabilityEmployee[]>;

  getByKey(caseId: number, monthYear: string, key: number): Promise<AvailabilityEmployee | null>;

  create(caseId: number, monthYear: string, entry: AvailabilityEmployee): Promise<void>;

  update(caseId: number, monthYear: string, key: number, data: Partial<AvailabilityEmployee>): Promise<void>;

  delete(caseId: number, monthYear: string, key: number): Promise<void>;
}
