"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Employee } from "@/entities/models/employee.model";
import { getAllEmployeesAction } from "@/features/employees/employees.actions";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";

interface EmployeeSelectorProps {
  value?: number; // employee key
  onSelect: (employee: Employee | null) => void;
  disabled?: boolean;
  excludedKeys?: number[]; // employee keys to exclude from the list
  caseId?: number;
  monthYear?: string;
}

export function EmployeeSelector({
  value,
  onSelect,
  disabled,
  excludedKeys = [],
  caseId: caseIdProp,
  monthYear: monthYearProp,
}: EmployeeSelectorProps) {
  const [open, setOpen] = React.useState(false);
  const [employees, setEmployees] = React.useState<Employee[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const searchParams = useSearchParams();
  const caseId = caseIdProp ?? parseInt(searchParams.get("caseId") ?? "0", 10);
  const monthYear = monthYearProp ?? searchParams.get("monthYear") ?? "";

  React.useEffect(() => {
    if (!caseId || !monthYear) return;
    setIsLoading(true);
    getAllEmployeesAction(caseId, monthYear)
      .then(setEmployees)
      .catch(() => setEmployees([]))
      .finally(() => setIsLoading(false));
  }, [caseId, monthYear]);

  // Filter out excluded employees
  const availableEmployees = employees.filter((emp) => !excludedKeys.includes(emp.key));

  const selectedEmployee = value ? employees.find((emp) => emp.key === value) : null;

  const displayEmployees = availableEmployees;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
          disabled={disabled || isLoading}
        >
          {selectedEmployee ? (
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className="truncate">
                {selectedEmployee.firstname} {selectedEmployee.name}
              </span>
              <Badge variant="outline" className="text-xs">
                {selectedEmployee.key}
              </Badge>
            </div>
          ) : (
            <span className="text-muted-foreground">{isLoading ? "Lädt..." : "Mitarbeiter auswählen..."}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(400px,calc(95vw-2rem))] p-0" align="start">
        <Command>
          <CommandInput placeholder="Mitarbeiter suchen..." />
          <CommandList
            className="h-[min(360px,50vh)] max-h-[50vh] overflow-y-scroll overscroll-contain"
            onWheel={(event) => event.stopPropagation()}
            onTouchMove={(event) => event.stopPropagation()}
          >
            <CommandEmpty>Keine Mitarbeiter gefunden.</CommandEmpty>
            <CommandGroup className="overflow-visible">
              {displayEmployees.map((employee) => (
                <CommandItem
                  key={employee.key}
                  value={`${employee.firstname} ${employee.name} ${employee.key}`}
                  onSelect={() => {
                    onSelect(value === employee.key ? null : employee);
                    setOpen(false);
                  }}
                >
                  <Check className={cn("mr-2 h-4 w-4", value === employee.key ? "opacity-100" : "opacity-0")} />
                  <div className="flex items-center justify-between flex-1 gap-2">
                    <span className="flex-1 truncate">
                      {employee.firstname} {employee.name}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="outline" className="text-xs">
                        {employee.key}
                      </Badge>
                      <span className="text-xs text-muted-foreground truncate max-w-[150px]">{employee.type}</span>
                    </div>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
