import {Employee} from '@/entities/models/employee.model';

export interface IEmployeeRepository {
    getAll(caseId: number, monthYear: string): Promise<Employee[]>;

    getByKey(caseId: number, monthYear: string, key: number): Promise<Employee | null>;

    create(caseId: number, monthYear: string, employee: Employee): Promise<void>;
}
