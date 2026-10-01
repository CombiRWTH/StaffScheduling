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
import {ViewMinimalStaffTemplateDialog} from '@/components/view-minimal-staff-template-dialog';
import {
    deleteMinimalStaffTemplateAction,
    getMinimalStaffTemplateAction,
    updateMinimalStaffTemplateAction,
} from '@/features/templates/minimal-staff-templates.actions';
import {Clock, Edit, Eye, FileText, Trash2, UserCog,} from 'lucide-react';
import {formatDistanceToNow} from 'date-fns';
import {de} from 'date-fns/locale';
import {TemplateSummary} from '@/entities/models/template.model';
import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {toast} from 'sonner';

interface MinimalStaffTemplatesPageClientProps {
    caseId: number;
    monthYear: string;
    templates: TemplateSummary[];
}

export function MinimalStaffTemplatesPageClient({caseId, monthYear, templates}: MinimalStaffTemplatesPageClientProps) {
    const [isUpdating, setIsUpdating] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const [editingTemplate, setEditingTemplate] = useState<{
        id: string;
        description: string;
    } | null>(null);

    const [viewingTemplateId, setViewingTemplateId] = useState<string | null>(null);
    const [viewingTemplateData, setViewingTemplateData] = useState<{
        description: string;
        content: MinimalStaffRequirements;
        last_modified: string;
    } | null>(null);

    const handleViewTemplate = async (templateId: string) => {
        setViewingTemplateId(templateId);
        const result = await getMinimalStaffTemplateAction(caseId, templateId);
        if (!result.success) {
            toast.error(result.error);
            return;
        }
        setViewingTemplateData({
            description: result.data._metadata.description,
            content: result.data.content,
            last_modified: result.data._metadata.last_modified,
        });
    };

    const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);

    const handleSaveDescription = async (newDescription: string) => {
        if (editingTemplate) {
            setIsUpdating(true);
            const result = await updateMinimalStaffTemplateAction(caseId, editingTemplate.id, {description: newDescription});
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
            const result = await deleteMinimalStaffTemplateAction(caseId, deletingTemplateId);
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
                                <UserCog className="h-6 w-6 text-primary"/>
                            </div>
                            <div>
                                <CardTitle>Mindestbesetzungs-Templates</CardTitle>
                                <CardDescription>
                                    Verwalten Sie Ihre gespeicherten Mindestbesetzungskonfigurationen
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
                                Speichern Sie Ihre erste Mindestbesetzungskonfiguration als Template auf der
                                Mindestbesetzungs-Seite.
                            </p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {templates.map((template) => (
                                <Card key={template.id} className="hover:bg-accent/5 transition-colors">
                                    <CardContent className="pt-6">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1 space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <FileText className="h-4 w-4 text-primary"/>
                                                    <h3 className="font-medium">{template.description}</h3>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Clock className="h-3.5 w-3.5"/>
                                                    <span>
                            Zuletzt geändert:{' '}
                                                        {formatDistanceToNow(new Date(template.last_modified), {
                                                            addSuffix: true,
                                                            locale: de,
                                                        })}
                          </span>
                                                </div>
                                                <div className="text-xs text-muted-foreground">ID: {template.id}</div>
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
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {editingTemplate && (
                <EditTemplateDescriptionDialog
                    open={!!editingTemplate}
                    onOpenChange={(open) => !open && setEditingTemplate(null)}
                    currentDescription={editingTemplate.description}
                    onSave={handleSaveDescription}
                    isSaving={isUpdating}
                />
            )}

            <ViewMinimalStaffTemplateDialog
                open={!!viewingTemplateId}
                onOpenChange={(open) => {
                    if (!open) {
                        setViewingTemplateId(null);
                        setViewingTemplateData(null);
                    }
                }}
                template={viewingTemplateData}
            />

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
