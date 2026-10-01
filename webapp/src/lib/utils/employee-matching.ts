/**
 * Employee matching utilities for template import.
 * Provides strict 3-field matching (key, firstname, name) for employee identification.
 */

import type { Employee } from "@/entities/models/employee.model";
import type { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";

/**
 * Result of matching template employees against current employees.
 */
export interface EmployeeMatchResult {
  /** Employees from template that were successfully matched */
  matched: Array<{
    templateEmployee: WishesAndBlockedEmployee;
    currentEmployee: Employee;
  }>;
  /** Employees from template that could not be matched */
  unmatched: WishesAndBlockedEmployee[];
  /** Number of successfully matched employees */
  matchCount: number;
  /** Total number of employees in the template */
  totalCount: number;
}

/**
 * Checks if two employees match based on strict 3-field comparison.
 * All three fields must match: key (exact), firstname (case-insensitive), name (case-insensitive).
 *
 * @param templateEmployee - Employee from the template
 * @param currentEmployee - Employee from the current case
 * @returns true if all three fields match
 */
export function employeesMatch(templateEmployee: WishesAndBlockedEmployee, currentEmployee: Employee): boolean {
  return (
    templateEmployee.key === currentEmployee.key &&
    templateEmployee.firstname.trim().toLowerCase() === currentEmployee.firstname.trim().toLowerCase() &&
    templateEmployee.name.trim().toLowerCase() === currentEmployee.name.trim().toLowerCase()
  );
}

/**
 * Matches a list of template employees against current employees.
 * Uses strict 3-field matching (key, firstname, name).
 *
 * @param templateEmployees - Array of employees from the template
 * @param currentEmployees - Array of employees in the current case
 * @returns Match result with matched and unmatched employees
 */
export function matchTemplateEmployees(
  templateEmployees: WishesAndBlockedEmployee[],
  currentEmployees: Employee[],
): EmployeeMatchResult {
  const matched: Array<{
    templateEmployee: WishesAndBlockedEmployee;
    currentEmployee: Employee;
  }> = [];
  const unmatched: WishesAndBlockedEmployee[] = [];

  for (const templateEmployee of templateEmployees) {
    const currentEmployee = currentEmployees.find((emp) => employeesMatch(templateEmployee, emp));

    if (currentEmployee) {
      matched.push({ templateEmployee, currentEmployee });
    } else {
      unmatched.push(templateEmployee);
    }
  }

  return {
    matched,
    unmatched,
    matchCount: matched.length,
    totalCount: templateEmployees.length,
  };
}

/**
 * Generates a summary string of employee names for display.
 * Example: "Alice Mueller, Bob Schmidt, Charlie Weber"
 *
 * @param employees - Array of employees or wishes/blocked employees
 * @param maxNames - Maximum number of names to show (default: 3)
 * @returns Formatted string of employee names
 */
export function getEmployeeNamesSummary(
  employees: Array<{ firstname: string; name: string }>,
  maxNames: number = 3,
): string {
  if (employees.length === 0) {
    return "Keine Mitarbeiter";
  }

  const names = employees.slice(0, maxNames).map((emp) => `${emp.firstname} ${emp.name}`);

  if (employees.length > maxNames) {
    names.push(`+${employees.length - maxNames} weitere`);
  }

  return names.join(", ");
}
