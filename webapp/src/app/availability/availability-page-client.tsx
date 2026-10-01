'use client';

import {useState, useTransition} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {Plus} from 'lucide-react';
import {toast} from 'sonner';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {AvailabilityDialog} from '@/features/availability/components/availability-dialog';
import {AvailabilityList} from '@/features/availability/components/availability-list';
import {
    createAvailabilityAction,
    deleteAvailabilityAction,
    updateAvailabilityAction,
} from '@/features/availability/availability.actions';
import {parseMonthYear} from '@/lib/utils/case-utils';
import type {AvailabilityEmployee} from '@/entities/models/availability.model';

interface AvailabilityCaseData {
    caseId: number;
    employees: AvailabilityEmployee[];
}

interface AvailabilityCaseError {
    caseId: number;
    error: string;
}

interface AvailabilityCaseCardProps {
    caseId: number;
    monthYear: string;
    employees: AvailabilityEmployee[];
}

interface AvailabilityPageClientProps {
    monthYear: string;
    availabilityCases: AvailabilityCaseData[];
    availabilityErrors: AvailabilityCaseError[];
    availableCaseIds: number[];
}

function AvailabilityCaseCard({caseId, monthYear, employees}: AvailabilityCaseCardProps) {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingEmployee, setEditingEmployee] = useState<AvailabilityEmployee | undefined>();
    const [isSubmitting, startSubmitTransition] = useTransition();
    const [isDeleting, startDeleteTransition] = useTransition();

    // Get list of employee keys that already have availability
    const existingEmployeeKeys = employees.map(employee => employee.key);
    const {month, year} = parseMonthYear(monthYear);
    const dayCount = new Date(year, month, 0).getDate();

    const handleCreate = () => {
        setEditingEmployee(undefined);
        setDialogOpen(true);
    };

    const handleEdit = (employee: AvailabilityEmployee) => {
        setEditingEmployee(employee);
        setDialogOpen(true);
    };

    const handleSubmit = async (data: AvailabilityEmployee) => {
        startSubmitTransition(async () => {
            let result;
            if (editingEmployee) {
                result = await updateAvailabilityAction(caseId, monthYear, editingEmployee.key, data);
            } else {
                result = await createAvailabilityAction(caseId, monthYear, data);
            }
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setDialogOpen(false);
            setEditingEmployee(undefined);
        });
    };

    const handleDelete = async (id: number) => {
        if (confirm('Möchtest du diesen Eintrag wirklich löschen?')) {
            startDeleteTransition(async () => {
                const result = await deleteAvailabilityAction(caseId, monthYear, id);
                if (!result.success) {
                    toast.error(result.error);
                }
            });
        }
    };

    return (
        <div className="py-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Availability für den Monat</CardTitle>
                            <CardDescription>
                                Case {caseId}: Verwalte verfügbare Tage für diesen Monat
                            </CardDescription>
                        </div>
                        <Button onClick={handleCreate}>
                            <Plus className="mr-2 h-4 w-4"/>
                            Neuer Eintrag
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    <AvailabilityList
                        employees={employees}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        isDeleting={isDeleting}
                        dayCount={dayCount}
                    />
                </CardContent>
            </Card>

            <AvailabilityDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                employee={editingEmployee}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                excludedEmployeeKeys={existingEmployeeKeys}
                caseId={caseId}
                monthYear={monthYear}
            />
        </div>
    );
}

export function AvailabilityPageClient({
                                           monthYear,
                                           availabilityCases,
                                           availabilityErrors,
                                           availableCaseIds,
                                       }: AvailabilityPageClientProps) {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();

    const visibleCaseIds = Array.from(
        new Set(
            (searchParams.get('caseIds') ?? searchParams.get('caseId') ?? '')
                .split(',')
                .map(id => Number(id))
                .filter(id => Number.isInteger(id) && id > 0)
        )
    );

    const sortedAvailableCaseIds = [...availableCaseIds].sort((a, b) => a - b);
    const visibleErrors = availabilityErrors.filter(({caseId}) => visibleCaseIds.includes(caseId));

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
        <div className="py-6 space-y-4">
            <Card>
                <CardHeader>
                    <CardTitle>Availability für den Monat</CardTitle>
                    <CardDescription>Wähle, welche Cases angezeigt werden sollen.</CardDescription>
                    <div className="flex flex-wrap gap-2 pt-2">
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
                </CardHeader>
            </Card>

            {visibleErrors.length > 0 && (
                <Alert variant="destructive">
                    <AlertTitle>Availability konnte nicht geladen werden</AlertTitle>
                    <AlertDescription>
                        {visibleErrors.map(({caseId, error}) => (
                            <div key={caseId}>Case {caseId}: {error}</div>
                        ))}
                    </AlertDescription>
                </Alert>
            )}

            {visibleCaseIds.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Wähle mindestens einen Case aus.</div>
            ) : availabilityCases.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Keine Availability gefunden.</div>
            ) : (
                availabilityCases.map(({caseId, employees}) => (
                    <AvailabilityCaseCard
                        key={caseId}
                        caseId={caseId}
                        monthYear={monthYear}
                        employees={employees}
                    />
                ))
            )}
        </div>
    );
}
