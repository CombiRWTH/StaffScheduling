'use client';

import {useState} from 'react';
import {Card, CardContent, CardDescription, CardHeader, CardTitle,} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
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
import {EditTemplateDescriptionDialog} from '@/components/edit-template-description-dialog';
import {
    deleteGlobalWishesTemplateAction,
    getGlobalWishesTemplateAction,
    updateGlobalWishesTemplateAction,
} from '@/features/templates/global-wishes-templates.actions';
import {Clock, Edit, Eye, FileText, Heart, Trash2, Users,} from 'lucide-react';
import {formatDistanceToNow} from 'date-fns';
import {de} from 'date-fns/locale';
import {Dialog, DialogContent, DialogHeader, DialogTitle} from '@/components/ui/dialog';
import {ScrollArea} from '@/components/ui/scroll-area';
import {
    GlobalWishesTemplateContent,
    GlobalWishesTemplateMetadata,
    Template,
    TemplateSummary,
} from '@/entities/models/template.model';
import {toast} from 'sonner';

interface GlobalWishesTemplatesPageClientProps {
    caseId: number;
    monthYear: string;
    templates: TemplateSummary[];
}

export function GlobalWishesTemplatesPageClient({caseId, monthYear, templates}: GlobalWishesTemplatesPageClientProps) {
    const [isUpdating, setIsUpdating] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const [editingTemplate, setEditingTemplate] = useState<{
        id: string;
        description: string;
    } | null>(null);

    const [viewingTemplateId, setViewingTemplateId] = useState<string | null>(null);
    const [viewingTemplate, setViewingTemplate] = useState<Template<GlobalWishesTemplateContent> | null>(null);

    const handleViewTemplate = async (templateId: string) => {
        setViewingTemplateId(templateId);
        const result = await getGlobalWishesTemplateAction(caseId, templateId);
        if (!result.success) {
            toast.error(result.error);
            return;
        }
        setViewingTemplate(result.data);
    };

    const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);

    const handleSaveDescription = async (newDescription: string) => {
        if (editingTemplate) {
            setIsUpdating(true);
            const result = await updateGlobalWishesTemplateAction(caseId, editingTemplate.id, {description: newDescription});
            setIsUpdating(false);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            toast.success('Template erfolgreich aktualisiert');
            setEditingTemplate(null);
        }
    };

    const handleDelete = async () => {
        if (deletingTemplateId) {
            setIsDeleting(true);
            const result = await deleteGlobalWishesTemplateAction(caseId, deletingTemplateId);
            setIsDeleting(false);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            toast.success('Template erfolgreich gelöscht');
            setDeletingTemplateId(null);
        }
    };

    return (
        <div className="py-6 space-y-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Heart className="h-6 w-6 text-primary"/>
                            </div>
                            <div>
                                <CardTitle>Globale Wünsche-Templates</CardTitle>
                                <CardDescription>
                                    Verwalten Sie Ihre gespeicherten Wunsch- und Blockierungskonfigurationen
                                </CardDescription>
                            </div>
                        </div>
                        <Badge variant="secondary">{templates.length} Templates</Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {templates.length === 0 ? (
                        <div className="text-center py-12">
                            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4"/>
                            <h3 className="text-lg font-medium mb-2">Keine Templates vorhanden</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Speichern Sie Ihre erste Wunsch-Konfiguration als Template auf der Globale
                                Wünsche & Blockierungen-Seite.
                            </p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {templates.map((template) => {
                                const metadata = template as unknown as GlobalWishesTemplateMetadata;
                                return (
                                    <Card key={template.id} className="hover:bg-accent/5 transition-colors">
                                        <CardContent className="pt-6">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1 space-y-2">
                                                    <div className="flex items-center gap-2">
                                                        <FileText className="h-4 w-4 text-primary"/>
                                                        <h3 className="font-medium">{template.description}</h3>
                                                    </div>
                                                    <div
                                                        className="flex items-center gap-4 text-sm text-muted-foreground">
                                                        <div className="flex items-center gap-2">
                                                            <Clock className="h-3.5 w-3.5"/>
                                                            <span>
                                {formatDistanceToNow(new Date(template.last_modified), {
                                    addSuffix: true,
                                    locale: de,
                                })}
                              </span>
                                                        </div>
                                                        {metadata.employeeCount && (
                                                            <div className="flex items-center gap-2">
                                                                <Users className="h-3.5 w-3.5"/>
                                                                <span>{metadata.employeeCount} Mitarbeiter</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div
                                                        className="text-xs text-muted-foreground">ID: {template.id}</div>
                                                </div>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleViewTemplate(template.id)}
                                                        disabled={isUpdating || isDeleting}
                                                    >
                                                        <Eye className="h-4 w-4"/>
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() =>
                                                            setEditingTemplate({
                                                                id: template.id,
                                                                description: template.description,
                                                            })
                                                        }
                                                        disabled={isUpdating || isDeleting}
                                                    >
                                                        <Edit className="h-4 w-4"/>
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setDeletingTemplateId(template.id)}
                                                        disabled={isUpdating || isDeleting}
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive"/>
                                                    </Button>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>

            {editingTemplate && (
                <EditTemplateDescriptionDialog
                    open={!!editingTemplate}
                    onOpenChange={(open) => !open && setEditingTemplate(null)}
                    currentDescription={editingTemplate?.description ?? ''}
                    onSave={handleSaveDescription}
                    isSaving={isUpdating}
                />
            )}

            <Dialog
                open={!!viewingTemplateId}
                onOpenChange={(open) => {
                    if (!open) {
                        setViewingTemplateId(null);
                        setViewingTemplate(null);
                    }
                }}
            >
                <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle>Template-Vorschau</DialogTitle>
                    </DialogHeader>
                    {viewingTemplate && (
                        <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
                            <div className="space-y-2">
                                <div className="text-sm text-muted-foreground">Beschreibung</div>
                                <div className="text-base">{viewingTemplate._metadata.description}</div>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Clock className="h-4 w-4"/>
                                    <span>
                    {formatDistanceToNow(new Date(viewingTemplate._metadata.last_modified), {
                        addSuffix: true,
                        locale: de,
                    })}
                  </span>
                                </div>
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Users className="h-4 w-4"/>
                                    <span>{viewingTemplate.content.employees.length} Mitarbeiter</span>
                                </div>
                            </div>

                            <div className="space-y-2 flex-1 overflow-hidden flex flex-col">
                                <div className="text-sm font-medium">Enthaltene Mitarbeiter</div>
                                <ScrollArea className="flex-1 rounded-md border">
                                    <div className="p-4 space-y-3">
                                        {viewingTemplate.content.employees.map((employee) => {
                                            const hasWishes =
                                                (employee.wish_days?.length ?? 0) > 0 || (employee.wish_shifts?.length ?? 0) > 0;
                                            const hasWork =
                                                (employee.work_days?.length ?? 0) > 0 || (employee.work_shifts?.length ?? 0) > 0;
                                            const hasBlocked =
                                                (employee.blocked_days?.length ?? 0) > 0 || (employee.blocked_shifts?.length ?? 0) > 0;

                                            return (
                                                <div
                                                    key={employee.key}
                                                    className="p-3 rounded-lg border bg-card space-y-2"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div className="font-medium">
                                                            {employee.firstname} {employee.name}
                                                        </div>
                                                        <Badge variant="outline" className="text-xs">
                                                            ID: {employee.key}
                                                        </Badge>
                                                    </div>
                                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                                                        <div>
                                                            <div className="text-muted-foreground mb-1">Wünsche</div>
                                                            {hasWishes ? (
                                                                <div className="space-y-1">
                                                                    {(employee.wish_days?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Tage: {employee.wish_days?.join(', ')}
                                                                        </div>
                                                                    )}
                                                                    {(employee.wish_shifts?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Schichten: {employee.wish_shifts?.length ?? 0}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ) : (
                                                                <div
                                                                    className="text-xs text-muted-foreground">Keine</div>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <div className="text-muted-foreground mb-1">Arbeitstage</div>
                                                            {hasWork ? (
                                                                <div className="space-y-1">
                                                                    {(employee.work_days?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Tage: {employee.work_days?.join(', ')}
                                                                        </div>
                                                                    )}
                                                                    {(employee.work_shifts?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Schichten: {employee.work_shifts?.length ?? 0}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ) : (
                                                                <div
                                                                    className="text-xs text-muted-foreground">Keine</div>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <div className="text-muted-foreground mb-1">Blockierungen
                                                            </div>
                                                            {hasBlocked ? (
                                                                <div className="space-y-1">
                                                                    {(employee.blocked_days?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Tage: {employee.blocked_days?.join(', ')}
                                                                        </div>
                                                                    )}
                                                                    {(employee.blocked_shifts?.length ?? 0) > 0 && (
                                                                        <div className="text-xs">
                                                                            Schichten: {employee.blocked_shifts?.length ?? 0}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ) : (
                                                                <div
                                                                    className="text-xs text-muted-foreground">Keine</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </ScrollArea>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            <AlertDialog
                open={!!deletingTemplateId}
                onOpenChange={(open) => !open && setDeletingTemplateId(null)}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Template löschen?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Sind Sie sicher, dass Sie dieses Template löschen möchten? Diese Aktion kann
                            nicht rückgängig gemacht werden.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDeleting}>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} disabled={isDeleting}>
                            Löschen
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
