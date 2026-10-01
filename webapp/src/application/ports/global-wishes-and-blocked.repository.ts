import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";

export interface IGlobalWishesAndBlockedRepository {
  getAll(caseId: number, monthYear: string): Promise<WishesAndBlockedEmployee[]>;

  getByKey(caseId: number, monthYear: string, key: number): Promise<WishesAndBlockedEmployee | null>;

  create(caseId: number, monthYear: string, entry: WishesAndBlockedEmployee): Promise<void>;

  update(caseId: number, monthYear: string, key: number, data: Partial<WishesAndBlockedEmployee>): Promise<void>;

  delete(caseId: number, monthYear: string, key: number): Promise<void>;
}
