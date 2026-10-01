import type {ICreateEmployeeUseCase} from '@/application/use-cases/employees/create-employee.use-case';
import type {Employee} from '@/entities/models/employee.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface ICreateEmployeeController {
    (input: { caseId: number; monthYear: string; employee: Employee }): Promise<
        { data: void } | { error: string }
    >;
}

export function makeCreateEmployeeController(
    createEmployeeUseCase: ICreateEmployeeUseCase
): ICreateEmployeeController {
    return async ({caseId, monthYear, employee}) => {
        try {
            validateMonthYear(monthYear);
            await createEmployeeUseCase({caseId, monthYear, employee});
            return {data: undefined};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
