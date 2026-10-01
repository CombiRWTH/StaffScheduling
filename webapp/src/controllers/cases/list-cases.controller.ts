import type { IListCasesUseCase } from "@/application/use-cases/cases/list-cases.use-case";
import type { CaseUnit } from "@/entities/models/case.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IListCasesController {
  (): Promise<{ data: CaseUnit[] } | { error: string }>;
}

export function makeListCasesController(listCasesUseCase: IListCasesUseCase): IListCasesController {
  return async () => {
    try {
      const cases = await listCasesUseCase();
      return { data: cases };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
