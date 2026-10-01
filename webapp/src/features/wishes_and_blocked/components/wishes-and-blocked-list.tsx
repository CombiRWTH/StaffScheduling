'use client';

import {useMemo, useState} from 'react';
import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow,} from '@/components/ui/table';
import {Button} from '@/components/ui/button';
import {Ban, Briefcase, Heart, Pencil, Search, Trash2} from 'lucide-react';
import {Badge} from '@/components/ui/badge';
import {Input} from '@/components/ui/input';

interface WishesAndBlockedListProps {
    employees: WishesAndBlockedEmployee[];
    onEdit: (employee: WishesAndBlockedEmployee) => void;
    onDelete: (id: number) => void;
    isDeleting?: boolean;
}

export function WishesAndBlockedList({
                                         employees,
                                         onEdit,
                                         onDelete,
                                         isDeleting
                                     }: WishesAndBlockedListProps) {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredEmployees = useMemo(() => {
        if (!searchTerm) return employees;

        const lowerSearch = searchTerm.toLowerCase();
        return employees.filter((employee) => {
            const fullName = `${employee.firstname} ${employee.name}`.toLowerCase();
            return fullName.includes(lowerSearch) ||
                employee.firstname.toLowerCase().includes(lowerSearch) ||
                employee.name.toLowerCase().includes(lowerSearch) ||
                employee.key.toString().includes(lowerSearch);
        });
    }, [employees, searchTerm]);

    if (employees.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                Keine Einträge vorhanden. Erstelle den ersten Eintrag!
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                    placeholder="Suche nach Name, Vorname oder ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                />
            </div>

            {filteredEmployees.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    Keine Einträge gefunden.
                </div>
            ) : (
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Mitarbeiter</TableHead>
                                <TableHead>Wünsche</TableHead>
                                <TableHead>Blockierungen</TableHead>
                                <TableHead className="text-right">Aktionen</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredEmployees.map((employee) => {
                                return (
                                    <TableRow key={employee.key}>
                                        <TableCell
                                            className="font-medium"
                                        >
                                            <div className="flex flex-col">
                                                <span>{employee.firstname} {employee.name}</span>
                                                <span
                                                    className="text-xs text-muted-foreground">ID: {employee.key}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <Heart className="h-4 w-4 text-blue-500"/>
                                                    <Badge variant="outline" className="bg-blue-100">
                                                        {employee.wish_days?.length ?? 0} Gewünschte freie Tage
                                                    </Badge>
                                                </div>

                                                <Badge variant="outline" className="bg-blue-50 ml-6">
                                                    {employee.wish_shifts?.length ?? 0} Gewünschte freie Schichten
                                                </Badge>

                                                <div className="flex items-center gap-2">
                                                    <Briefcase className="h-4 w-4 text-green-500"/>
                                                    <Badge variant="outline" className="bg-green-100">
                                                        {employee.work_days?.length ?? 0} Gewünschte Arbeitstage
                                                    </Badge>
                                                </div>

                                                <Badge variant="outline" className="bg-green-50 ml-6">
                                                    {employee.work_shifts?.length ?? 0} Gewünschte Arbeitsschichten
                                                </Badge>

                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <Ban className="h-4 w-4 text-red-500"/>
                                                    <Badge variant="outline" className="bg-red-100">
                                                        {employee.blocked_days?.length ?? 0} Blockierte Tage
                                                    </Badge>
                                                </div>

                                                <Badge variant="outline" className="bg-red-50 ml-6">
                                                    {employee.blocked_shifts?.length ?? 0} Blockierte Schichten
                                                </Badge>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => onEdit(employee)}
                                                title="Bearbeiten"
                                            >
                                                <Pencil className="h-4 w-4"/>
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => onDelete(employee.key)}
                                                disabled={isDeleting}
                                                title="Löschen"
                                            >
                                                <Trash2 className="h-4 w-4"/>
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
