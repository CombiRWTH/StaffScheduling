"use client";

import { useMemo, useState } from "react";
import { CalendarX, Clock, Minus, Pencil, Search, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";

interface AvailabilityListProps {
  employees: AvailabilityEmployee[];
  onEdit: (employee: AvailabilityEmployee) => void;
  onDelete: (id: number) => void;
  isDeleting?: boolean;
  dayCount?: number;
}

export function AvailabilityList({ employees, onEdit, onDelete, isDeleting, dayCount }: AvailabilityListProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredEmployees = useMemo(() => {
    if (!searchTerm) return employees;

    const lowerSearch = searchTerm.toLowerCase();
    return employees.filter((employee) => {
      const fullName = `${employee.firstname} ${employee.name}`.toLowerCase();
      return (
        fullName.includes(lowerSearch) ||
        employee.firstname.toLowerCase().includes(lowerSearch) ||
        employee.name.toLowerCase().includes(lowerSearch) ||
        employee.key.toString().includes(lowerSearch)
      );
    });
  }, [employees, searchTerm]);

  if (employees.length === 0) {
    return <div className="text-center py-12 text-muted-foreground">Keine Availability-Einträge vorhanden.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Suche nach Name, Vorname oder ID..."
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          className="pl-9"
        />
      </div>

      {filteredEmployees.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Keine Einträge gefunden.</div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mitarbeiter</TableHead>
                <TableHead>Availability</TableHead>
                <TableHead className="text-right">Aktionen</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => {
                const unavailableDayCount = employee.unavailability_days?.length ?? 0;
                const unavailableShiftCount = employee.unavailability_shifts?.length ?? 0;
                const neutralDayCount =
                  dayCount === undefined ? undefined : Math.max(0, dayCount - unavailableDayCount);

                return (
                  <TableRow key={employee.key}>
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        <span>
                          {employee.firstname} {employee.name}
                        </span>
                        <span className="text-xs text-muted-foreground">ID: {employee.key}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <CalendarX className="h-4 w-4 text-red-500" />
                          <Badge variant="outline" className="bg-red-100">
                            {unavailableDayCount} Nicht verfügbare Tage
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-red-400" />
                          <Badge variant="outline" className="bg-red-50">
                            {unavailableShiftCount} Nicht verfügbare Schichten
                          </Badge>
                        </div>
                        {neutralDayCount !== undefined && (
                          <div className="flex items-center gap-2">
                            <Minus className="h-4 w-4 text-slate-500" />
                            <Badge variant="outline">{neutralDayCount} Nicht ausgewählte Tage</Badge>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="ghost" size="icon" onClick={() => onEdit(employee)} title="Bearbeiten">
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onDelete(employee.key)}
                        disabled={isDeleting}
                        title="Löschen"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
