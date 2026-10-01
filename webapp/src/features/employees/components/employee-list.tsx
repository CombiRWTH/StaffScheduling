'use client';

import {useMemo, useState} from 'react';
import {Employee} from '@/entities/models/employee.model';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow,} from '@/components/ui/table';
import {Badge} from "@/components/ui/badge";
import {Input} from "@/components/ui/input";
import {Search} from 'lucide-react';
import {filterEmployees} from "@/features/employees/utils/filter-employees";

interface EmployeeListProps {
    employees: Employee[];
}

export function EmployeeList({
                                 employees
                             }: EmployeeListProps) {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredEmployees = useMemo(
        () => filterEmployees(employees, searchTerm),
        [employees, searchTerm]
    );

    if (employees.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                Keine Mitarbeiter vorhanden.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                    placeholder="Suche nach Name, Vorname, Beruf oder ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                />
            </div>

            {filteredEmployees.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    Keine Mitarbeiter gefunden.
                </div>
            ) : (
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>ID</TableHead>
                                <TableHead>Vorname</TableHead>
                                <TableHead>Nachname</TableHead>
                                <TableHead>Beruf</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredEmployees.map((employee) => (
                                <TableRow
                                    key={employee.key}
                                >
                                    <TableCell><Badge>{employee.key}</Badge></TableCell>
                                    <TableCell className="font-medium">
                                        {employee.firstname}
                                    </TableCell>
                                    <TableCell>{employee.name}</TableCell>
                                    <TableCell>{employee.type}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}

        </div>
    );
}
