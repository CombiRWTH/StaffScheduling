"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { de } from "date-fns/locale";
import { CalendarCheck, Clock, Eye, Pencil, Trash2, Users } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EditTemplateDescriptionDialog } from "@/components/edit-template-description-dialog";
import {
  deleteAvailabilityTemplateAction,
  getAvailabilityTemplateAction,
  updateAvailabilityTemplateAction,
} from "@/features/templates/availability-templates.actions";
import type { AvailabilityTemplateContent, Template, TemplateSummary } from "@/entities/models/template.model";

interface AvailabilityTemplatesPageClientProps {
  caseId: number;
  monthYear: string;
  templates: TemplateSummary[];
}

export function AvailabilityTemplatesPageClient({ caseId, templates }: AvailabilityTemplatesPageClientProps) {
  const [editingTemplate, setEditingTemplate] = useState<{ id: string; description: string } | null>(null);
  const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);
  const [viewingTemplateId, setViewingTemplateId] = useState<string | null>(null);
  const [viewingTemplate, setViewingTemplate] = useState<Template<AvailabilityTemplateContent> | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleViewTemplate = async (templateId: string) => {
    setViewingTemplateId(templateId);
    const result = await getAvailabilityTemplateAction(caseId, templateId);
    if (!result.success) {
      toast.error(result.error);
      setViewingTemplateId(null);
      return;
    }
    setViewingTemplate(result.data);
  };

  const handleUpdateDescription = async (newDescription: string) => {
    if (!editingTemplate) return;
    const result = await updateAvailabilityTemplateAction(caseId, editingTemplate.id, { description: newDescription });
    if (!result.success) {
      toast.error(result.error);
      return;
    }
    toast.success("Template erfolgreich aktualisiert");
    setEditingTemplate(null);
  };

  const handleDelete = async () => {
    if (!deletingTemplateId) return;
    setIsDeleting(true);
    const result = await deleteAvailabilityTemplateAction(caseId, deletingTemplateId);
    setIsDeleting(false);
    if (!result.success) {
      toast.error(result.error);
      return;
    }
    toast.success("Template erfolgreich gelöscht");
    setDeletingTemplateId(null);
  };

  return (
    <div className="py-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Availability-Templates</CardTitle>
              <CardDescription>Verwalte gespeicherte globale Availability-Konfigurationen</CardDescription>
            </div>
            <Badge variant="secondary">{templates.length} Templates</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {templates.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CalendarCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">Keine Templates vorhanden</h3>
              <p>Speichere deine erste Availability-Konfiguration auf der Global Availability-Seite.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {templates.map((template) => (
                <Card key={template.id} className="hover:bg-accent/5 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        <div className="p-2 bg-primary/10 rounded-lg shrink-0">
                          <CalendarCheck className="h-5 w-5 text-primary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium truncate">{template.description}</h3>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5" />
                              {formatDistanceToNow(new Date(template.last_modified), {
                                addSuffix: true,
                                locale: de,
                              })}
                            </div>
                            <div className="text-xs">ID: {template.id}</div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewTemplate(template.id)}
                          title="Anzeigen"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setEditingTemplate({
                              id: template.id,
                              description: template.description,
                            })
                          }
                          title="Beschreibung bearbeiten"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeletingTemplateId(template.id)}
                          title="Löschen"
                        >
                          <Trash2 className="h-4 w-4" />
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
          onSave={handleUpdateDescription}
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
        <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
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
                  <Clock className="h-4 w-4" />
                  <span>
                    {formatDistanceToNow(new Date(viewingTemplate._metadata.last_modified), {
                      addSuffix: true,
                      locale: de,
                    })}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>{viewingTemplate.content.employees.length} Mitarbeiter</span>
                </div>
              </div>
              <ScrollArea className="flex-1 rounded-md border">
                <div className="p-4 space-y-3">
                  {viewingTemplate.content.employees.map((employee) => (
                    <div key={employee.key} className="p-3 rounded-lg border bg-card space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="font-medium">
                          {employee.firstname} {employee.name}
                        </div>
                        <Badge variant="outline" className="text-xs">
                          ID: {employee.key}
                        </Badge>
                      </div>
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <div>
                          Nicht verfügbare Tage:{" "}
                          {(employee.unavailability_days?.length ?? 0) > 0
                            ? employee.unavailability_days?.join(", ")
                            : "Keine"}
                        </div>
                        <div>
                          Nicht verfügbare Schichten:{" "}
                          {(employee.unavailability_shifts?.length ?? 0) > 0
                            ? employee.unavailability_shifts?.map(([day, shift]) => `${day}-${shift}`).join(", ")
                            : "Keine"}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deletingTemplateId} onOpenChange={(open) => !open && setDeletingTemplateId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Template löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Sind Sie sicher, dass Sie dieses Template löschen möchten? Diese Aktion kann nicht rückgängig gemacht
              werden.
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
