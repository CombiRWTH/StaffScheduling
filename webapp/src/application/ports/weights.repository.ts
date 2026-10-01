import {Weights} from '@/entities/models/weights.model';

export interface IWeightsRepository {
    get(caseId: number, monthYear: string): Promise<Weights>;

    update(caseId: number, monthYear: string, weights: Weights): Promise<void>;
}
