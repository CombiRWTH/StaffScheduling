import type { ICreateWishesUseCase } from "@/application/use-cases/wishes-and-blocked/create-wishes.use-case";
import type { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface ICreateWishesController {
  (input: {
    caseId: number;
    monthYear: string;
    entry: WishesAndBlockedEmployee;
  }): Promise<{ data: void } | { error: string }>;
}

export function makeCreateWishesController(createWishesUseCase: ICreateWishesUseCase): ICreateWishesController {
  return async ({ caseId, monthYear, entry }) => {
    try {
      validateMonthYear(monthYear);
      await createWishesUseCase({ caseId, monthYear, entry });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
