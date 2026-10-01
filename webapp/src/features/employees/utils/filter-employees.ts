import {Employee} from "@/entities/models";

export function filterEmployees<T extends Employee & { caseId?: number }>(employees: T[], searchTerm: string): T[] {
    if (!searchTerm) return employees;

    const lowerSearch = searchTerm.toLowerCase();
    return employees.filter((employee) => {
        const fullName = `${employee.firstname} ${employee.name}`.toLowerCase();
        const caseId = employee.caseId?.toString() ?? '';
        return fullName.includes(lowerSearch) ||
            employee.firstname.toLowerCase().includes(lowerSearch) ||
            employee.name.toLowerCase().includes(lowerSearch) ||
            employee.type.toLowerCase().includes(lowerSearch) ||
            employee.key.toString().includes(lowerSearch) ||
            caseId.includes(lowerSearch);
    });
}
