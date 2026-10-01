import type { IDeleteGlobalWishesUseCase } from "@/application/use-cases/global-wishes/delete-global-wishes.use-case";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IDeleteGlobalWishesController {
  (input: { caseId: number; monthYear: string; key: number }): Promise<{ data: void } | { error: string }>;
}

export function makeDeleteGlobalWishesController(
  deleteGlobalWishesUseCase: IDeleteGlobalWishesUseCase,
): IDeleteGlobalWishesController {
  return async ({ caseId, monthYear, key }) => {
    try {
      validateMonthYear(monthYear);
      await deleteGlobalWishesUseCase({ caseId, monthYear, key });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
