import { IGlobalWishesTemplateRepository } from "@/application/ports/global-wishes-template.repository";
import { GlobalWishesTemplateContent, Template } from "@/entities/models/template.model";
import { TemplateNotFoundError } from "@/entities/errors/template.errors";

export interface IUpdateGlobalWishesTemplateUseCase {
  (input: {
    caseId: number;
    templateId: string;
    data: { content?: GlobalWishesTemplateContent; description?: string };
  }): Promise<Template<GlobalWishesTemplateContent>>;
}

export function makeUpdateGlobalWishesTemplateUseCase(
  repository: IGlobalWishesTemplateRepository,
): IUpdateGlobalWishesTemplateUseCase {
  return async ({ caseId, templateId, data }) => {
    try {
      return await repository.update(caseId, templateId, data);
    } catch {
      throw new TemplateNotFoundError(templateId);
    }
  };
}
