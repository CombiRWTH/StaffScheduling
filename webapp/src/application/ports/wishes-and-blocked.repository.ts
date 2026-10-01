import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";

export interface IWishesAndBlockedRepository {
  getAll(caseId: number, monthYear: string): Promise<WishesAndBlockedEmployee[]>;

  getByKey(caseId: number, monthYear: string, key: number): Promise<WishesAndBlockedEmployee | null>;

  create(caseId: number, monthYear: string, entry: WishesAndBlockedEmployee): Promise<void>;

  update(caseId: number, monthYear: string, key: number, data: Partial<WishesAndBlockedEmployee>): Promise<void>;

  delete(caseId: number, monthYear: string, key: number): Promise<void>;

  /** Delete all monthly-wishes entries for the given case/month. */
  deleteAll(caseId: number, monthYear: string): Promise<void>;

  /**
   * Generate (create or overwrite) the monthly wishes entry for one employee
   * from their global (weekly) pattern.
   */
  generateFromGlobal(caseId: number, monthYear: string, globalEntry: WishesAndBlockedEmployee): Promise<void>;
}
