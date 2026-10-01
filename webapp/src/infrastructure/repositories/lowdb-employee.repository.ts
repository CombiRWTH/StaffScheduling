import {IEmployeeRepository} from '@/application/ports/employee.repository';
import {Employee} from '@/entities/models/employee.model';
import {getEmployeeDb} from '@/infrastructure/persistence/lowdb/employees.db';

export class LowdbEmployeeRepository implements IEmployeeRepository {
    async getAll(caseId: number, monthYear: string): Promise<Employee[]> {
        const db = await getEmployeeDb(caseId, monthYear);
        return db.data.employees;
    }

    async getByKey(caseId: number, monthYear: string, key: number): Promise<Employee | null> {
        const db = await getEmployeeDb(caseId, monthYear);
        return db.data.employees.find((e) => e.key === key) ?? null;
    }

    async create(caseId: number, monthYear: string, employee: Employee): Promise<void> {
        const db = await getEmployeeDb(caseId, monthYear);
        db.data.employees.push(employee);
        await db.write();
    }
}
