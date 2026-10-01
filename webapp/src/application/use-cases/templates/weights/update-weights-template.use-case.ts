import { IWeightsTemplateRepository } from "@/application/ports/weights-template.repository";
import { Template } from "@/entities/models/template.model";
import { Weights } from "@/entities/models/weights.model";
import { TemplateNotFoundError } from "@/entities/errors/template.errors";

export interface IUpdateWeightsTemplateUseCase {
  (input: {
    caseId: number;
    templateId: string;
    data: { content?: Weights; description?: string };
  }): Promise<Template<Weights>>;
}

export function makeUpdateWeightsTemplateUseCase(
  repository: IWeightsTemplateRepository,
): IUpdateWeightsTemplateUseCase {
  return async ({ caseId, templateId, data }) => {
    try {
      return await repository.update(caseId, templateId, data);
    } catch {
      throw new TemplateNotFoundError(templateId);
    }
  };
}
