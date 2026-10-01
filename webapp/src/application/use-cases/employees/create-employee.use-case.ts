import { Employee } from "@/entities/models/employee.model";
import { IEmployeeRepository } from "@/application/ports/employee.repository";

export interface ICreateEmployeeUseCase {
  (input: { caseId: number; monthYear: string; employee: Employee }): Promise<void>;
}

export function makeCreateEmployeeUseCase(employeeRepository: IEmployeeRepository): ICreateEmployeeUseCase {
  return async ({ caseId, monthYear, employee }) => {
    return employeeRepository.create(caseId, monthYear, employee);
  };
}
