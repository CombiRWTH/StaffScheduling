'use client';

import {useState, useTransition} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Plus, Save, Upload} from 'lucide-react';
import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {WishesAndBlockedList} from '@/features/wishes_and_blocked/components/wishes-and-blocked-list';
import {WishesAndBlockedDialog} from '@/features/wishes_and_blocked/components/wishes-and-blocked-dialog';
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

import {
    createGlobalWishesAction,
    deleteGlobalWishesAction,
    importGlobalWishesTemplateAction,
    updateGlobalWishesAction,
} from '@/features/global_wishes_and_blocked/global-wishes-and-blocked.actions';
import {SaveTemplateDialog} from '@/components/save-template-dialog';
import {ImportGlobalWishesTemplateDialog} from '@/components/import-global-wishes-template-dialog';
import {
    createGlobalWishesTemplateAction,
    getGlobalWishesTemplateAction
} from '@/features/templates/global-wishes-templates.actions';
import {Employee} from '@/entities/models/employee.model';
import {GlobalWishesTemplateContent, Template, TemplateSummary} from '@/entities/models/template.model';
import {toast} from 'sonner';

interface GlobalWishesAndBlockedPageClientProps {
    caseId: number;
    monthYear: string;
    employees: WishesAndBlockedEmployee[];
    currentEmployees: Employee[];
    templates: TemplateSummary[];
}

interface GlobalWishesCaseData {
    caseId: number;
    employees: WishesAndBlockedEmployee[];
    currentEmployees: Employee[];
    templates: TemplateSummary[];
}

interface GlobalWishesCaseError {
    caseId: number;
    error: string;
}

interface GlobalWishesAndBlockedMultiCasePageClientProps {
    monthYear: string;
    globalWishesCases: GlobalWishesCaseData[];
    globalWishesErrors: GlobalWishesCaseError[];
    availableCaseIds: number[];
}

/**
 * Client component for managing *global* wishes and blocked periods.
 *
 * This view is shown inside a case for a given month/year and allows the
 * user to create, edit and delete global wish/blocked entries for employees.
 * It also integrates template operations so that common configurations can
 * be persisted and applied across months.
 *
 * Props:
 *  - caseId: numeric identifier of the case (used by backend actions)
 *  - monthYear: string representation of the target month ("MM_YYYY")
 *  - employees: list of existing global entries for the month
 *  - currentEmployees: full directory of employees used to resolve keys
 *  - templates: summaries of available global-wishes templates for this case
 */
function GlobalWishesAndBlockedCaseCard({
    caseId,
    monthYear,
    employees,
    currentEmployees,
    templates,
}: GlobalWishesAndBlockedPageClientProps) {
    // dialog state for the add/edit form
    const [dialogOpen, setDialogOpen] = useState(false);
    // currently edited entry when editing; undefined when creating new
    const [editingEmployee, setEditingEmployee] = useState<WishesAndBlockedEmployee | undefined>();
    // transitions for async actions to keep UI responsive
    const [isSubmitting, startSubmitTransition] = useTransition();
    const [isDeleting, startDeleteTransition] = useTransition();

    // ---------- Template-related state and helpers ----------
    // Controls visibility of the "save as template" dialog
    const [saveTemplateDialogOpen, setSaveTemplateDialogOpen] = useState(false);
    // Controls visibility of the "import template" dialog
    const [importTemplateDialogOpen, setImportTemplateDialogOpen] = useState(false);

    // content of a template that has been loaded for previewing inside the
    // import dialog; null when no template is selected
    const [selectedTemplate, setSelectedTemplate] = useState<Template<GlobalWishesTemplateContent> | null>(null);

    // transitions for various template operations
    const [isCreatingTemplate, startCreateTemplateTransition] = useTransition();
    const [isImporting, startImportTransition] = useTransition();
    const [, startLoadTemplateTransition] = useTransition();

    // Confirmation dialog for saving a change.  The save operation has side
    // effects: it resets the monthly wishes, so we ask the user to confirm.
    const [confirmSaveOpen, setConfirmSaveOpen] = useState(false);
    const [pendingEntry, setPendingEntry] = useState<{
        entry: WishesAndBlockedEmployee;
        isEdit: boolean;
    } | null>(null);

    // When deleting, we also show a confirmation; we store the ID of the entry
    // to delete (or null if none is pending)
    const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

    // user clicked "New entry" - clear any existing editing state
    const handleCreate = () => {
        setEditingEmployee(undefined);
        setDialogOpen(true);
    };

    // user clicked edit on a row - populate the form with that employee
    const handleEdit = (employee: WishesAndBlockedEmployee) => {
        setEditingEmployee(employee);
        setDialogOpen(true);
    };

    /**
     * Form submission handler triggered by the dialog component.
     *
     * Because the dialog only collects the human-readable name we must convert
     * it to the internal key.  When creating, the key is looked up in the
     * currentEmployees list; when editing, we already know the key.
     * Once we have a fully formed entry we stash it in `pendingEntry` and open
     * the confirmation dialog instead of immediately calling the backend.
     */
    const handleSubmit = (data: Omit<WishesAndBlockedEmployee, 'key'>) => {
        const isEdit = !!editingEmployee;

        let key: number;
        if (isEdit) {
            // editing existing entry - preserve its key
            key = editingEmployee!.key;
        } else {
            // create: locate the employee by name
            const found = currentEmployees.find(
                (e) => e.firstname === data.firstname && e.name === data.name
            );
            if (!found) {
                toast.error('Mitarbeiter nicht gefunden.');
                return;
            }
            key = found.key;
        }

        setPendingEntry({entry: {key, ...data}, isEdit});
        setDialogOpen(false);
        setConfirmSaveOpen(true);
    };

    /**
     * User confirmed the save operation in the dialog.  Dispatches the
     * appropriate create or update action and shows a toast result.  Note that
     * both flows include the message about resetting monthly wishes since the
     * backend will recompute them.
     */
    const handleConfirmSave = async () => {
        if (!pendingEntry) return;
        const {entry, isEdit} = pendingEntry;
        startSubmitTransition(async () => {
            let result;
            if (isEdit) {
                const {key, ...data} = entry;
                result = await updateGlobalWishesAction(caseId, monthYear, key, data);
            } else {
                result = await createGlobalWishesAction(caseId, monthYear, entry);
            }
            if (!result.success) {
                toast.error(result.error);
            } else if (isEdit) {
                toast.success('Globale Wünsche gespeichert. Monatliche Wünsche wurden zurückgesetzt.');
            } else {
                toast.success('Globale Wünsche erstellt. Monatliche Wünsche wurden neu berechnet.');
            }
            setPendingEntry(null);
            setEditingEmployee(undefined);
        });
    };

    // when the delete button is pressed, open the confirmation dialog
    const handleDeleteRequest = (id: number) => {
        setConfirmDeleteId(id);
    };

    // actually perform deletion after user confirms
    const handleConfirmDelete = async () => {
        if (confirmDeleteId === null) return;
        startDeleteTransition(async () => {
            const result = await deleteGlobalWishesAction(caseId, monthYear, confirmDeleteId);
            if (!result.success) {
                toast.error(result.error);
            } else {
                toast.success('Eintrag und zugehörige monatliche Wünsche wurden gelöscht.');
            }
            setConfirmDeleteId(null);
        });
    };

    // Template handlers
    /**
     * Gather the current global wishes entries and send them to the server as a
     * new template.  The description is provided by the save dialog.
     */
    const handleSaveAsTemplate = (description: string) => {
        const content = {
            employees: employees.map((emp: WishesAndBlockedEmployee) => ({
                key: emp.key,
                firstname: emp.firstname,
                name: emp.name,
                wish_days: emp.wish_days ?? [],
                wish_shifts: emp.wish_shifts ?? [],
                work_days: emp.work_days ?? [],
                work_shifts: emp.work_shifts ?? [],
                blocked_days: emp.blocked_days ?? [],
                blocked_shifts: emp.blocked_shifts ?? [],
            })),
        };

        startCreateTemplateTransition(async () => {
            const result = await createGlobalWishesTemplateAction(caseId, content, description);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setSaveTemplateDialogOpen(false);
            toast.success(`Template "${description}" wurde erfolgreich gespeichert.`);
        });
    };

    // loads the full template data when user selects an entry in the
    // import dialog; this allows previewing before import
    const handleSelectTemplate = (templateId: string) => {
        startLoadTemplateTransition(async () => {
            const result = await getGlobalWishesTemplateAction(caseId, templateId);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setSelectedTemplate(result.data);
        });
    };

    /**
     * Import the selected template into the current month.  The backend returns
     * a summary of how many entries matched, which we display in a toast.
     */
    const handleImport = async (templateId: string) => {
        startImportTransition(async () => {
            const result = await importGlobalWishesTemplateAction(caseId, monthYear, templateId);
            if (!result.success) {
                toast.error(`Fehler beim Importieren: ${result.error}`);
                return;
            }
            const {matchCount, totalCount, unmatchedCount} = result.data;
            toast.success(
                `Template importiert: ${matchCount} von ${totalCount} Mitarbeiter wurden importiert.` +
                (unmatchedCount > 0 ? ` ${unmatchedCount} Mitarbeiter wurden übersprungen.` : '')
            );
            setImportTemplateDialogOpen(false);
            setSelectedTemplate(null);
        });
    };

    const pendingEmployeeName = pendingEntry
        ? `${pendingEntry.entry.firstname} ${pendingEntry.entry.name}`
        : '';

    return (
        <div className="py-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Globale Wünsche & Blockierungen</CardTitle>
                            <CardDescription>
                                Case {caseId}: Verwalte monatsübergreifende freie und blockierte Tage und Schichten
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
                            <Button onClick={handleCreate}>
                                <Plus className="mr-2 h-4 w-4"/>
                                Neuer Eintrag
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <WishesAndBlockedList
                        employees={employees}
                        onEdit={handleEdit}
                        onDelete={handleDeleteRequest}
                        isDeleting={isDeleting}
                    />
                </CardContent>
            </Card>

            <WishesAndBlockedDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                employee={editingEmployee}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                isGlobal={true}
                caseId={caseId}
                monthYear={monthYear}
            />

            {/* Confirmation: save creates/edits a gw entry → resets mw */}
            <AlertDialog open={confirmSaveOpen} onOpenChange={setConfirmSaveOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Monatliche Wünsche werden zurückgesetzt</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die Wünsche für <strong>{pendingEmployeeName}</strong> in diesem Monat werden gelöscht
                            und aus den globalen Wünschen neu berechnet. Fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => setPendingEntry(null)}>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmSave}>Speichern</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Confirmation: delete gw entry also deletes mw */}
            <AlertDialog
                open={confirmDeleteId !== null}
                onOpenChange={(open) => {
                    if (!open) setConfirmDeleteId(null);
                }}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Eintrag löschen</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die globalen <strong>und</strong> monatlichen Wünsche für diesen Mitarbeiter
                            werden unwiderruflich gelöscht. Fortfahren?
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

            <SaveTemplateDialog
                open={saveTemplateDialogOpen}
                onOpenChange={setSaveTemplateDialogOpen}
                onSave={handleSaveAsTemplate}
                isSaving={isCreatingTemplate}
            />

            <ImportGlobalWishesTemplateDialog
                open={importTemplateDialogOpen}
                onOpenChange={(open) => {
                    setImportTemplateDialogOpen(open);
                    if (!open) setSelectedTemplate(null);
                }}
                templates={templates}
                selectedTemplateContent={selectedTemplate}
                currentEmployees={currentEmployees}
                onImport={handleImport}
                onSelectTemplate={handleSelectTemplate}
                isImporting={isImporting}
            />
        </div>
    );
}

export function GlobalWishesAndBlockedPageClient({
    monthYear,
    globalWishesCases,
    globalWishesErrors,
    availableCaseIds,
}: GlobalWishesAndBlockedMultiCasePageClientProps) {
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
    const visibleErrors = globalWishesErrors.filter(({caseId}) => visibleCaseIds.includes(caseId));

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
                    <CardTitle>Globale Wünsche & Blockierungen</CardTitle>
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
                    <AlertTitle>Globale Wünsche konnten nicht geladen werden</AlertTitle>
                    <AlertDescription>
                        {visibleErrors.map(({caseId, error}) => (
                            <div key={caseId}>Case {caseId}: {error}</div>
                        ))}
                    </AlertDescription>
                </Alert>
            )}

            {visibleCaseIds.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Wähle mindestens einen Case aus.</div>
            ) : globalWishesCases.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">Keine globalen Wünsche gefunden.</div>
            ) : (
                globalWishesCases.map(({caseId, employees, currentEmployees, templates}) => (
                    <GlobalWishesAndBlockedCaseCard
                        key={caseId}
                        caseId={caseId}
                        monthYear={monthYear}
                        employees={employees}
                        currentEmployees={currentEmployees}
                        templates={templates}
                    />
                ))
            )}
        </div>
    );
}
