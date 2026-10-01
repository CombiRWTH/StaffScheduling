import { IGlobalWishesTemplateRepository } from "@/application/ports/global-wishes-template.repository";
import { TemplateNotFoundError } from "@/entities/errors/template.errors";

export interface IDeleteGlobalWishesTemplateUseCase {
  (input: { caseId: number; templateId: string }): Promise<void>;
}

export function makeDeleteGlobalWishesTemplateUseCase(
  repository: IGlobalWishesTemplateRepository,
): IDeleteGlobalWishesTemplateUseCase {
  return async ({ caseId, templateId }) => {
    try {
      await repository.delete(caseId, templateId);
    } catch {
      throw new TemplateNotFoundError(templateId);
    }
  };
}
