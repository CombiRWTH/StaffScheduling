import type { IGetGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/get-global-wishes-template.use-case";
import type { GlobalWishesTemplateContent, Template } from "@/entities/models/template.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IGetGlobalWishesTemplateController {
  (input: {
    caseId: number;
    templateId: string;
  }): Promise<{ data: Template<GlobalWishesTemplateContent> } | { error: string }>;
}

export function makeGetGlobalWishesTemplateController(
  getGlobalWishesTemplateUseCase: IGetGlobalWishesTemplateUseCase,
): IGetGlobalWishesTemplateController {
  return async ({ caseId, templateId }) => {
    try {
      const template = await getGlobalWishesTemplateUseCase({ caseId, templateId });
      return { data: template };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
