import { Weights } from "@/entities/models/weights.model";
import { IWeightsRepository } from "@/application/ports/weights.repository";

export interface IGetWeightsUseCase {
  (input: { caseId: number; monthYear: string }): Promise<Weights>;
}

export function makeGetWeightsUseCase(weightsRepository: IWeightsRepository): IGetWeightsUseCase {
  return async ({ caseId, monthYear }) => {
    return weightsRepository.get(caseId, monthYear);
  };
}
