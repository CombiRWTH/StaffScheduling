import { IWeightsTemplateRepository } from "@/application/ports/weights-template.repository";
import { Template } from "@/entities/models/template.model";
import { Weights } from "@/entities/models/weights.model";
import { TemplateNotFoundError } from "@/entities/errors/template.errors";

export interface IGetWeightsTemplateUseCase {
  (input: { caseId: number; templateId: string }): Promise<Template<Weights>>;
}

export function makeGetWeightsTemplateUseCase(repository: IWeightsTemplateRepository): IGetWeightsTemplateUseCase {
  return async ({ caseId, templateId }) => {
    try {
      return await repository.get(caseId, templateId);
    } catch {
      throw new TemplateNotFoundError(templateId);
    }
  };
}
