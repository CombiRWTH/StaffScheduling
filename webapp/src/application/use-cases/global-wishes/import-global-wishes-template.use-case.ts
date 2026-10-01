import type { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";
import type { IGlobalWishesTemplateRepository } from "@/application/ports/global-wishes-template.repository";
import type { IEmployeeRepository } from "@/application/ports/employee.repository";
import type { IWishesAndBlockedRepository } from "@/application/ports/wishes-and-blocked.repository";
import { matchTemplateEmployees } from "@/lib/utils/employee-matching";
import { ValidationError } from "@/entities/errors/base.errors";

export interface ImportGlobalWishesTemplateInput {
  caseId: number;
  monthYear: string;
  templateId: string;
}

export interface ImportGlobalWishesTemplateResult {
  matchCount: number;
  totalCount: number;
  unmatchedCount: number;
}

export interface IImportGlobalWishesTemplateUseCase {
  (input: ImportGlobalWishesTemplateInput): Promise<ImportGlobalWishesTemplateResult>;
}

export function makeImportGlobalWishesTemplateUseCase(
  globalWishesRepository: IGlobalWishesAndBlockedRepository,
  templateRepository: IGlobalWishesTemplateRepository,
  employeeRepository: IEmployeeRepository,
  wishesRepository: IWishesAndBlockedRepository,
): IImportGlobalWishesTemplateUseCase {
  return async ({ caseId, monthYear, templateId }) => {
    const [template, currentEmployees, existingGlobalWishes] = await Promise.all([
      templateRepository.get(caseId, templateId),
      employeeRepository.getAll(caseId, monthYear),
      globalWishesRepository.getAll(caseId, monthYear),
    ]);

    const matchResult = matchTemplateEmployees(template.content.employees, currentEmployees);

    if (matchResult.matchCount === 0) {
      throw new ValidationError(
        "Keine passenden Mitarbeiter gefunden. Es wurden keine Mitarbeiter gefunden, die importiert werden können.",
      );
    }

    // Always perform a full reset: delete all monthly wishes and global wishes first
    await wishesRepository.deleteAll(caseId, monthYear);
    for (const emp of existingGlobalWishes) {
      await globalWishesRepository.delete(caseId, monthYear, emp.key);
    }

    // Create global wishes from template and generate fresh monthly entries
    for (const { templateEmployee, currentEmployee } of matchResult.matched) {
      const entry = {
        key: currentEmployee.key,
        firstname: templateEmployee.firstname,
        name: templateEmployee.name,
        wish_days: templateEmployee.wish_days ?? [],
        wish_shifts: templateEmployee.wish_shifts ?? [],
        work_days: templateEmployee.work_days ?? [],
        work_shifts: templateEmployee.work_shifts ?? [],
        blocked_days: templateEmployee.blocked_days ?? [],
        blocked_shifts: templateEmployee.blocked_shifts ?? [],
      };
      await globalWishesRepository.create(caseId, monthYear, entry);
      await wishesRepository.generateFromGlobal(caseId, monthYear, entry);
    }

    return {
      matchCount: matchResult.matchCount,
      totalCount: matchResult.totalCount,
      unmatchedCount: matchResult.unmatched.length,
    };
  };
}
