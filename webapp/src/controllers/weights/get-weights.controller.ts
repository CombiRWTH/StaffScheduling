import type {IGetWeightsUseCase} from '@/application/use-cases/weights/get-weights.use-case';
import type {Weights} from '@/entities/models/weights.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IGetWeightsController {
    (input: { caseId: number; monthYear: string }): Promise<
        { data: Weights } | { error: string }
    >;
}

export function makeGetWeightsController(
    getWeightsUseCase: IGetWeightsUseCase
): IGetWeightsController {
    return async ({caseId, monthYear}) => {
        try {
            validateMonthYear(monthYear);
            const weights = await getWeightsUseCase({caseId, monthYear});
            return {data: weights};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
