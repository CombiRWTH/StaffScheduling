"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { AlertCircle, CheckCircle2, Clock, FileText, Loader2, TriangleAlert, Users, XCircle } from "lucide-react";
import { GlobalWishesTemplateContent, Template, TemplateSummary } from "@/entities/models/template.model";
import { Employee } from "@/entities/models/employee.model";
import { format, formatDistanceToNow } from "date-fns";
import { de } from "date-fns/locale";
import { matchTemplateEmployees } from "@/lib/utils/employee-matching";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ImportGlobalWishesTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templates: TemplateSummary[];
  selectedTemplateContent?: Template<GlobalWishesTemplateContent> | null;
  currentEmployees: Employee[];
  onImport: (templateId: string) => void;
  onSelectTemplate: (templateId: string) => void;
  isImporting?: boolean;
}

/**
 * Dialog for importing global wishes templates with employee matching preview.
 * Always performs a full reset: all existing global and monthly wishes are deleted
 * before importing from the template.
 */
export function ImportGlobalWishesTemplateDialog({
  open,
  onOpenChange,
  templates,
  selectedTemplateContent,
  currentEmployees,
  onImport,
  onSelectTemplate,
  isImporting = false,
}: ImportGlobalWishesTemplateDialogProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");

  const handleSelectTemplate = (templateId: string) => {
    setSelectedTemplateId(templateId);
    onSelectTemplate(templateId);
  };

  const handleImport = () => {
    if (selectedTemplateId) {
      onImport(selectedTemplateId);
    }
  };

  const handleCancel = () => {
    setSelectedTemplateId("");
    onOpenChange(false);
  };

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  // Calculate matching results when template content is loaded
  const matchResult = selectedTemplateContent
    ? matchTemplateEmployees(selectedTemplateContent.content.employees, currentEmployees)
    : null;

  const truncate = (text: string, max = 60) => {
    if (!text) return "";
    return text.length > max ? text.slice(0, max - 1) + "â€¦" : text;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Template laden</DialogTitle>
          <DialogDescription>
            Wählen Sie ein Template für die globalen Wünsche aus. Es werden nur Wünsche für Mitarbeiter importiert, die
            im aktuellen Monat vorhanden sind.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 flex-1 overflow-hidden">
          {/* Warning about full reset */}
          <div className="rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/20 p-3 flex items-start gap-2">
            <TriangleAlert className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-800 dark:text-amber-200">
              <strong>Achtung:</strong> Alle bestehenden globalen und monatlichen Wünsche werden vollständig gelöscht
              und durch die Daten aus dem Template ersetzt.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="template-select">Template auswählen</Label>
            <Select value={selectedTemplateId} onValueChange={handleSelectTemplate} disabled={isImporting}>
              <SelectTrigger id="template-select" className="w-full">
                <SelectValue placeholder="Wählen Sie ein Template..." />
              </SelectTrigger>
              <SelectContent className="w-full" align="start">
                {templates.map((template) => {
                  const metadata = template as unknown as {
                    employeeCount?: number;
                    employeeIds?: number[];
                  };
                  return (
                    <SelectItem key={template.id} value={template.id}>
                      <div className="flex items-center gap-2 w-full">
                        <FileText className="h-3.5 w-3.5" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-3">
                            <span className="block text-sm truncate">{truncate(template.description, 35)}</span>
                            <div className="flex items-center gap-2">
                              {metadata.employeeCount && (
                                <Badge variant="secondary" className="text-xs">
                                  <Users className="h-3 w-3 mr-1" />
                                  {metadata.employeeCount}
                                </Badge>
                              )}
                              <span className="text-xs text-muted-foreground whitespace-nowrap">
                                {format(new Date(template.last_modified), "dd.MM.yyyy", { locale: de })}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {selectedTemplate && !selectedTemplateContent && (
            <div className="rounded-lg border p-3 bg-muted/50 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span>
                  Zuletzt geändert:{" "}
                  {formatDistanceToNow(new Date(selectedTemplate.last_modified), {
                    addSuffix: true,
                    locale: de,
                  })}
                </span>
              </div>
              <p className="text-sm">{selectedTemplate.description}</p>
            </div>
          )}

          {matchResult && selectedTemplateContent && (
            <div className="space-y-3 flex-1 overflow-hidden flex flex-col">
              <div className="rounded-lg border p-4 bg-muted/50 space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  <span>
                    {formatDistanceToNow(new Date(selectedTemplateContent._metadata.last_modified), {
                      addSuffix: true,
                      locale: de,
                    })}
                  </span>
                </div>
                <p className="text-sm">{selectedTemplateContent._metadata.description}</p>

                <div className="flex items-center gap-4 pt-2">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                      {matchResult.matchCount} von {matchResult.totalCount} Mitarbeiter gefunden
                    </span>
                  </div>
                  {matchResult.matchCount < matchResult.totalCount && (
                    <Badge variant="outline" className="text-xs">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      {matchResult.totalCount - matchResult.matchCount} werden Ã¼bersprungen
                    </Badge>
                  )}
                </div>
              </div>

              <div className="space-y-2 flex-1 overflow-hidden flex flex-col">
                <Label>Mitarbeiter-Matching</Label>
                <ScrollArea className="flex-1 rounded-md border">
                  <div className="p-3 space-y-2">
                    {matchResult.matched.length > 0 && (
                      <div className="space-y-1">
                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                          Gefundene Mitarbeiter ({matchResult.matched.length})
                        </div>
                        {matchResult.matched.map(({ templateEmployee, currentEmployee }) => (
                          <div
                            key={templateEmployee.key}
                            className="flex items-center gap-2 p-2 rounded-md bg-green-50 dark:bg-green-950/20 text-sm"
                          >
                            <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-500 shrink-0" />
                            <span className="flex-1">
                              {currentEmployee.firstname} {currentEmployee.name}
                            </span>
                            <Badge variant="secondary" className="text-xs">
                              ID: {currentEmployee.key}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}

                    {matchResult.unmatched.length > 0 && (
                      <div className="space-y-1 mt-3">
                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                          Nicht gefundene Mitarbeiter ({matchResult.unmatched.length})
                        </div>
                        {matchResult.unmatched.map((employee) => (
                          <div
                            key={employee.key}
                            className="flex items-center gap-2 p-2 rounded-md bg-amber-50 dark:bg-amber-950/20 text-sm"
                          >
                            <XCircle className="h-4 w-4 text-amber-600 dark:text-amber-500 shrink-0" />
                            <span className="flex-1 text-muted-foreground">
                              {employee.firstname} {employee.name}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              ID: {employee.key}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={isImporting}>
            Abbrechen
          </Button>
          {matchResult && (
            <Button onClick={handleImport} disabled={isImporting || matchResult.matchCount === 0}>
              {isImporting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Importieren ({matchResult.matchCount})
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
