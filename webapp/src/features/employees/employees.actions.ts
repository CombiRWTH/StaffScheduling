'use server';

import {getInjection} from '@/di/container';
import {Employee} from '@/entities/models/employee.model';

export async function getAllEmployeesAction(caseId: number, monthYear: string): Promise<Employee[]> {
    const controller = getInjection('IGetAllEmployeesController');
    const result = await controller({caseId, monthYear});
    if ('error' in result) throw new Error(result.error);
    return result.data;
}

export async function getEmployeeByKeyAction(caseId: number, monthYear: string, key: number): Promise<Employee | null> {
    const controller = getInjection('IGetEmployeeController');
    const result = await controller({caseId, monthYear, key});
    if ('error' in result) return null;
    return result.data;
}
