"use client";

import { useRouter } from "next/navigation";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

/** Chooses the employee; the selection lives in the URL next to month and stations. */
export function EmployeePicker({
  href,
  employees,
  selectedId,
}: {
  /** The page URL with the current selection, without `employee`. */
  href: string;
  employees: { employee_id: number; display_name: string }[];
  selectedId: number;
}) {
  const router = useRouter();

  return (
    <div className="flex items-center gap-3">
      <Label htmlFor="employee-picker">Mitarbeiter</Label>
      <Select value={String(selectedId)} onValueChange={(value) => router.push(`${href}&employee=${value}`)}>
        <SelectTrigger id="employee-picker" className="w-72" aria-label="Mitarbeiter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {employees.map(({ employee_id, display_name }) => (
            <SelectItem key={employee_id} value={String(employee_id)}>
              {employee_id} · {display_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
