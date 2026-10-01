'use client';

import {useState, useTransition} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {Plus} from 'lucide-react';
import {Save, Upload} from 'lucide-react';
import {toast} from 'sonner';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {AvailabilityDialog} from '@/features/availability/components/availability-dialog';
import {AvailabilityList} from '@/features/availability/components/availability-list';
import {ImportTemplateDialog} from '@/components/import-template-dialog';
import {SaveTemplateDialog} from '@/components/save-template-dialog';
import {
    createGlobalAvailabilityAction,
    deleteGlobalAvailabilityAction,
    importAvailabilityTemplateAction,
    updateGlobalAvailabilityAction,
} from '@/features/availability/availability.actions';
import {createAvailabilityTemplateAction} from '@/features/templates/availability-templates.actions';
import type {AvailabilityEmployee} from '@/entities/models/availability.model';
import type {TemplateSummary} from '@/entities/models/template.model';

interface GlobalAvailabilityCaseData {
    caseId: number;
    employees: AvailabilityEmployee[];
    templates: TemplateSummary[];
}

interface GlobalAvailabilityCaseError {
    caseId: number;
    error: string;
}

interface GlobalAvailabilityCaseCardProps {
    caseId: number;
    monthYear: string;
    employees: AvailabilityEmployee[];
    templates: TemplateSummary[];
}

interface GlobalAvailabilityPageClientProps {
    monthYear: string;
    globalAvailabilityCases: GlobalAvailabilityCaseData[];
    globalAvailabilityErrors: GlobalAvailabilityCaseError[];
    availableCaseIds: number[];
}

function GlobalAvailabilityCaseCard({caseId, monthYear, employees, templates}: GlobalAvailabilityCaseCardProps) {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [saveTemplateDialogOpen, setSaveTemplateDialogOpen] = useState(false);
    const [importTemplateDialogOpen, setImportTemplateDialogOpen] = useState(false);
    const [editingEmployee, setEditingEmployee] = useState<AvailabilityEmployee | undefined>();
    const [pendingEntry, setPendingEntry] = useState<{ entry: AvailabilityEmployee; isEdit: boolean } | null>(null);
    const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
    const [isSubmitting, startSubmitTransition] = useTransition();
    const [isDeleting, startDeleteTransition] = useTransition();
    const [isCreatingTemplate, startCreateTemplateTransition] = useTransition();
    const [isImportingTemplate, startImportTemplateTransition] = useTransition();
    const existingEmployeeKeys = employees.map(employee => employee.key);

    const handleSubmit = (data: AvailabilityEmployee) => {
        setPendingEntry({entry: data, isEdit: !!editingEmployee});
        setDialogOpen(false);
    };

    const handleConfirmSave = () => {
        if (!pendingEntry) return;

        startSubmitTransition(async () => {
            const result = pendingEntry.isEdit && editingEmployee
                ? await updateGlobalAvailabilityAction(caseId, monthYear, editingEmployee.key, pendingEntry.entry)
                : await createGlobalAvailabilityAction(caseId, monthYear, pendingEntry.entry);

            if (!result.success) {
                toast.error(result.error);
            } else {
                toast.success('Globale Availability gespeichert. Monatliche Availability wurde neu berechnet.');
            }

            setPendingEntry(null);
            setEditingEmployee(undefined);
        });
    };

    const handleConfirmDelete = () => {
        if (confirmDeleteId === null) return;

        startDeleteTransition(async () => {
            const result = await deleteGlobalAvailabilityAction(caseId, monthYear, confirmDeleteId);
            if (!result.success) toast.error(result.error);
            setConfirmDeleteId(null);
        });
    };

    const pendingEmployeeName = pendingEntry
        ? `${pendingEntry.entry.firstname} ${pendingEntry.entry.name}`
        : '';

    const handleSaveAsTemplate = (description: string) => {
        startCreateTemplateTransition(async () => {
            const result = await createAvailabilityTemplateAction(caseId, {employees}, description);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setSaveTemplateDialogOpen(false);
            toast.success(`Template "${description}" wurde erfolgreich gespeichert.`);
        });
    };

    const handleImportTemplate = (templateId: string) => {
        startImportTemplateTransition(async () => {
            const result = await importAvailabilityTemplateAction(caseId, monthYear, templateId);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setImportTemplateDialogOpen(false);
            toast.success(`Template importiert: ${result.data.importedCount} Mitarbeiter.`);
        });
    };

    return (
        <div className="py-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Globale Availability</CardTitle>
                            <CardDescription>
                                Case {caseId}: Verwalte monatsübergreifende verfügbare Wochentage
                            </CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => setImportTemplateDialogOpen(true)}
                                disabled={templates.length === 0}
                            >
                                <Upload className="mr-2 h-4 w-4"/>
                                Template laden
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setSaveTemplateDialogOpen(true)}
                                disabled={employees.length === 0}
                            >
                                <Save className="mr-2 h-4 w-4"/>
                                Als Template speichern
                            </Button>
                            <Button
                                onClick={() => {
                                    setEditingEmployee(undefined);
                                    setDialogOpen(true);
                                }}
                            >
                                <Plus className="mr-2 h-4 w-4"/>
                                Neuer Eintrag
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <AvailabilityList
                        employees={employees}
                        onEdit={(employee) => {
                            setEditingEmployee(employee);
                            setDialogOpen(true);
                        }}
                        onDelete={setConfirmDeleteId}
                        isDeleting={isDeleting}
                        dayCount={7}
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
                isGlobal
                caseId={caseId}
                monthYear={monthYear}
            />

            <SaveTemplateDialog
                open={saveTemplateDialogOpen}
                onOpenChange={setSaveTemplateDialogOpen}
                onSave={handleSaveAsTemplate}
                isSaving={isCreatingTemplate}
            />

            <ImportTemplateDialog
                open={importTemplateDialogOpen}
                onOpenChange={setImportTemplateDialogOpen}
                templates={templates}
                onImport={handleImportTemplate}
                isImporting={isImportingTemplate}
                title="Availability-Template laden"
            />

            <AlertDialog open={!!pendingEntry} onOpenChange={(open) => !open && setPendingEntry(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Monatliche Availability wird neu berechnet</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die Availability für <strong>{pendingEmployeeName}</strong> in diesem Monat wird aus
                            der globalen Availability neu berechnet. Fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => setPendingEntry(null)}>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmSave}>Speichern</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <AlertDialog
                open={confirmDeleteId !== null}
                onOpenChange={(open) => {
                    if (!open) setConfirmDeleteId(null);
                }}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Availability löschen</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die globale und monatliche Availability für diesen Mitarbeiter wird gelöscht. Fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Löschen
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

export function GlobalAvailabilityPageClient({
                                                 monthYear,
                                                 globalAvailabilityCases,
                                                 globalAvailabilityErrors,
                                                 availableCaseIds,
                                             }: GlobalAvailabilityPageClientProps) {
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
    const visibleErrors = globalAvailabilityErrors.filter(({caseId}) => visibleCaseIds.includes(caseId));

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
                    <CardTitle>Globale Availability</CardTitle>
                    <CardDescription>Wähle, welche Cases angezeigt werden sollen.</CardDescription>
                    <div className="flex flex-wrap gap-2 pt-2">
                        {sortedAvailableCaseIds.map(caseId => (
                            <Button
                                key={caseId}
                                type="button"
                                size="sm"
                                variant={visibleCaseIds.includes(caseId) ? 'default' : 'outline'}
                                onClick={() => toggleCase(caseId)}
                            >
                                Case {caseId}
                            </Button>
                        ))}
                    </div>
                </CardHeader>
            </Card>

            {visibleErrors.length > 0 && (
                <Alert variant="destructive">
                    <AlertTitle>Globale Availability konnte nicht geladen werden</AlertTitle>
                    <AlertDescription>
                        {visibleErrors.map(({caseId, error}) => (
                            <div key={caseId}>Case {caseId}: {error}</div>
                        ))}
                    </AlertDescription>
                </Alert>
            )}

            {visibleCaseIds.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Wähle mindestens einen Case aus.</div>
            ) : globalAvailabilityCases.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Keine globale Availability gefunden.</div>
            ) : (
                globalAvailabilityCases.map(({caseId, employees, templates}) => (
                    <GlobalAvailabilityCaseCard
                        key={caseId}
                        caseId={caseId}
                        monthYear={monthYear}
                        employees={employees}
                        templates={templates}
                    />
                ))
            )}
        </div>
    );
}
