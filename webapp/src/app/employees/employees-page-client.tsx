'use client';

import {useMemo, useState} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Employee} from '@/entities/models/employee.model';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';
import {Badge} from '@/components/ui/badge';
import {Input} from '@/components/ui/input';
import {Search} from 'lucide-react';
import {filterEmployees} from '@/features/employees/utils/filter-employees';
import {Button} from '@/components/ui/button';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';

interface EmployeeCaseData {
    caseId: number;
    employees: Employee[];
}

interface EmployeeCaseError {
    caseId: number;
    error: string;
}

interface EmployeeRow extends Employee {
    caseId: number;
}

interface EmployeesPageClientProps {
    employeeCases: EmployeeCaseData[];
    employeeErrors: EmployeeCaseError[];
    availableCaseIds: number[];
}

export function EmployeesPageClient({employeeCases, employeeErrors, availableCaseIds}: EmployeesPageClientProps) {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();
    const [searchTerm, setSearchTerm] = useState('');

    const visibleCaseIds = useMemo(() => {
        const caseIdsParam = searchParams.get('caseIds') ?? searchParams.get('caseId') ?? '';
        return Array.from(
            new Set(
                caseIdsParam
                    .split(',')
                    .map(id => Number(id))
                    .filter(id => Number.isInteger(id) && id > 0)
            )
        );
    }, [searchParams]);

    const visibleCases = useMemo(
        () => employeeCases.filter(({caseId}) => visibleCaseIds.includes(caseId)),
        [employeeCases, visibleCaseIds]
    );

    const visibleErrors = useMemo(
        () => employeeErrors.filter(({caseId}) => visibleCaseIds.includes(caseId)),
        [employeeErrors, visibleCaseIds]
    );

    const sortedAvailableCaseIds = useMemo(
        () => [...availableCaseIds].sort((a, b) => a - b),
        [availableCaseIds]
    );

    const rows = useMemo<EmployeeRow[]>(
        () =>
            visibleCases.flatMap(({caseId, employees}) =>
                employees.map(employee => ({
                    ...employee,
                    caseId,
                }))
            ),
        [visibleCases]
    );

    const filteredRows = useMemo(() => {
        return filterEmployees(rows, searchTerm).sort((a, b) => {
            if (a.caseId !== b.caseId) {
                return a.caseId - b.caseId;
            }

            const lastNameCompare = a.name.localeCompare(b.name, 'de', {sensitivity: 'base'});
            if (lastNameCompare !== 0) {
                return lastNameCompare;
            }

            const firstNameCompare = a.firstname.localeCompare(b.firstname, 'de', {sensitivity: 'base'});
            if (firstNameCompare !== 0) {
                return firstNameCompare;
            }

            return a.key - b.key;
        });
    }, [rows, searchTerm]);

    const toggleCase = (caseId: number) => {
        const nextCaseIds = visibleCaseIds.includes(caseId)
            ? visibleCaseIds.filter(id => id !== caseId)
            : [...visibleCaseIds, caseId];

        const params = new URLSearchParams(searchParams.toString());

        if (nextCaseIds.length > 0) {
            params.set('caseIds', nextCaseIds.join(','));
            params.set('caseId', String(nextCaseIds[0]));
        } else {
            params.delete('caseIds');
            params.delete('caseId');
        }

        router.push(`${pathname}?${params.toString()}`);
    };

    return (
        <div className="py-6">
            <Card>
                <CardHeader>
                    <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between gap-4">
                            <div>
                                <CardTitle>Mitarbeiter-Datenbank</CardTitle>
                                <CardDescription>
                                    Wähle, welche Cases angezeigt werden sollen
                                </CardDescription>
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {sortedAvailableCaseIds.map(caseId => {
                                const active = visibleCaseIds.includes(caseId);

                                return (
                                    <Button
                                        key={caseId}
                                        type="button"
                                        size="sm"
                                        variant={active ? 'default' : 'outline'}
                                        onClick={() => toggleCase(caseId)}
                                    >
                                        Case {caseId}
                                    </Button>
                                );
                            })}
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {visibleErrors.length > 0 && (
                        <Alert variant="destructive">
                            <AlertTitle>Mitarbeiter konnten nicht geladen werden</AlertTitle>
                            <AlertDescription>
                                {visibleErrors.map(({caseId, error}) => (
                                    <div key={caseId}>
                                        Case {caseId}: {error}
                                    </div>
                                ))}
                            </AlertDescription>
                        </Alert>
                    )}

                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                        <Input
                            placeholder="Suche nach Name, Vorname, Beruf, Case oder ID..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-9"
                        />
                    </div>

                    {visibleCaseIds.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            Wähle mindestens einen Case aus.
                        </div>
                    ) : filteredRows.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            Keine Mitarbeiter gefunden.
                        </div>
                    ) : (
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Case</TableHead>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Vorname</TableHead>
                                        <TableHead>Nachname</TableHead>
                                        <TableHead>Beruf</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredRows.map((employee) => (
                                        <TableRow key={`${employee.caseId}-${employee.key}`}>
                                            <TableCell>
                                                <Badge variant="secondary">Case {employee.caseId}</Badge>
                                            </TableCell>
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
                </CardContent>
            </Card>
        </div>
    );
}
