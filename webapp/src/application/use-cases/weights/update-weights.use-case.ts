import { Weights } from "@/entities/models/weights.model";
import { IWeightsRepository } from "@/application/ports/weights.repository";

export interface IUpdateWeightsUseCase {
  (input: { caseId: number; monthYear: string; weights: Weights }): Promise<void>;
}

export function makeUpdateWeightsUseCase(weightsRepository: IWeightsRepository): IUpdateWeightsUseCase {
  return async ({ caseId, monthYear, weights }) => {
    return weightsRepository.update(caseId, monthYear, weights);
  };
}
