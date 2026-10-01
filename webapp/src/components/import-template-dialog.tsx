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
import { Clock, FileText, Loader2 } from "lucide-react";
import { TemplateSummary } from "@/entities/models/template.model";
import { format, formatDistanceToNow } from "date-fns";
import { de } from "date-fns/locale";

interface ImportTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templates: TemplateSummary[];
  onImport: (templateId: string) => void;
  isImporting?: boolean;
  title?: string;
}

/**
 * Dialog for importing/loading a template.
 */
export function ImportTemplateDialog({
  open,
  onOpenChange,
  templates,
  onImport,
  isImporting = false,
  title = "Template laden",
}: ImportTemplateDialogProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");

  const handleImport = () => {
    if (selectedTemplateId) {
      onImport(selectedTemplateId);
      setSelectedTemplateId("");
    }
  };

  const handleCancel = () => {
    setSelectedTemplateId("");
    onOpenChange(false);
  };

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  const truncate = (text: string, max = 60) => {
    if (!text) return "";
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            Wählen Sie ein Template aus, um die aktuellen Einstellungen zu ersetzen.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="template-select">Template auswählen</Label>
            <Select value={selectedTemplateId} onValueChange={setSelectedTemplateId} disabled={isImporting}>
              <SelectTrigger id="template-select" className="w-full">
                <SelectValue placeholder="Wählen Sie ein Template..." />
              </SelectTrigger>
              <SelectContent className="w-full" align="start">
                {templates.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    <div className="flex items-center gap-2 w-full">
                      <FileText className="h-3.5 w-3.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-3">
                          <span className="block text-sm truncate">{truncate(template.description, 40)}</span>
                          <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                            {format(new Date(template.last_modified), "dd.MM.yyyy HH:mm", { locale: de })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedTemplate && (
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
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={isImporting}>
            Abbrechen
          </Button>
          <Button onClick={handleImport} disabled={!selectedTemplateId || isImporting}>
            {isImporting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Laden
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
