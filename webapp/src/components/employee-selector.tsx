"use client";
import type { Employee } from "@/entities/models/employee.model";

interface EmployeeSelectorProps {
  value?: number;
  onSelect: (employee: Employee | null) => void;
  disabled?: boolean;
  excludedKeys?: number[];
  caseId?: number;
  monthYear?: string;
}
export const EmployeeSelector: React.FC<EmployeeSelectorProps> = () => {
  return (
    <p role="status">
      Mitarbeiter-Eingaben in dieser bisherigen Konfigurationsansicht werden noch nicht unterstützt. Die aktuelle
      Mitarbeiterprüfung ist über die Navigation verfügbar.
    </p>
  );
};
