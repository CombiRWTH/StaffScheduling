import type { ICreateGlobalWishesTemplateUseCase } from "@/application/use-cases/templates/global-wishes/create-global-wishes-template.use-case";
import type { GlobalWishesTemplateContent, TemplateSummary } from "@/entities/models/template.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface ICreateGlobalWishesTemplateController {
  (input: {
    caseId: number;
    content: GlobalWishesTemplateContent;
    description: string;
  }): Promise<{ data: TemplateSummary } | { error: string }>;
}

export function makeCreateGlobalWishesTemplateController(
  createGlobalWishesTemplateUseCase: ICreateGlobalWishesTemplateUseCase,
): ICreateGlobalWishesTemplateController {
  return async ({ caseId, content, description }) => {
    try {
      const summary = await createGlobalWishesTemplateUseCase({ caseId, content, description });
      return { data: summary };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
