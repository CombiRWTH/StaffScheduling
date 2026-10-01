import {Employee} from '@/entities/models/employee.model';
import {EmployeeNotFoundError} from '@/entities/errors/employee.errors';
import {IEmployeeRepository} from '@/application/ports/employee.repository';

export interface IGetEmployeeUseCase {
    (input: { caseId: number; monthYear: string; key: number }): Promise<Employee>;
}

export function makeGetEmployeeUseCase(
    employeeRepository: IEmployeeRepository
): IGetEmployeeUseCase {
    return async ({caseId, monthYear, key}) => {
        const employee = await employeeRepository.getByKey(caseId, monthYear, key);
        if (!employee) throw new EmployeeNotFoundError(key);
        return employee;
    };
}
