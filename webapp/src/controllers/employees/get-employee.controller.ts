import type {IGetEmployeeUseCase} from '@/application/use-cases/employees/get-employee.use-case';
import type {Employee} from '@/entities/models/employee.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IGetEmployeeController {
    (input: { caseId: number; monthYear: string; key: number }): Promise<
        { data: Employee } | { error: string }
    >;
}

export function makeGetEmployeeController(
    getEmployeeUseCase: IGetEmployeeUseCase
): IGetEmployeeController {
    return async ({caseId, monthYear, key}) => {
        try {
            validateMonthYear(monthYear);
            const employee = await getEmployeeUseCase({caseId, monthYear, key});
            return {data: employee};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
