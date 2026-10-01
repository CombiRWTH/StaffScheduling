"use client";

import {useState} from "react";
import {SchedulesMetadata} from "@/entities/models/schedule.model";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select";
import {Button} from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {Badge} from "@/components/ui/badge";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Calendar, Check, CheckCircle, Loader2, Pencil, Save, Trash2} from "lucide-react";
import {toast} from "sonner";
import {Checkbox} from "@/components/ui/checkbox";
import {Textarea} from "@/components/ui/textarea";

interface ScheduleSelectorProps {
    schedulesMetadata: SchedulesMetadata;
    onScheduleSelect: (scheduleId: string) => Promise<void>;
    onScheduleDelete: (scheduleId: string) => Promise<void>;
    onScheduleSave: (scheduleId: string) => Promise<void>;
    onRefresh?: () => Promise<void>;
    selectedScheduleIds?: string[];
    onMultipleSchedulesSelect?: (scheduleIds: string[]) => void;
    compareMode?: boolean;
    onDescriptionUpdate?: (scheduleId: string, description: string) => Promise<void>;
}

export function ScheduleSelector({
                                     schedulesMetadata,
                                     onScheduleSelect,
                                     onScheduleDelete,
                                     onScheduleSave,
                                     onRefresh,
                                     selectedScheduleIds = [],
                                     onMultipleSchedulesSelect,
                                     compareMode = false,
                                     onDescriptionUpdate,
                                 }: ScheduleSelectorProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [editingDescriptionId, setEditingDescriptionId] = useState<string | null>(null);
    const [editingDescription, setEditingDescription] = useState<string>("");
    const [savingScheduleId, setSavingScheduleId] = useState<string | null>(null);

    const handleSelect = async (scheduleId: string) => {
        try {
            setIsLoading(true);
            await onScheduleSelect(scheduleId);
            toast.success("Dienstplan ausgewählt");
            if (onRefresh) await onRefresh();
        } catch (error) {
            toast.error("Fehler beim Auswählen des Dienstplans");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (scheduleId: string) => {
        if (!confirm("Möchten Sie diesen Dienstplan wirklich löschen?")) {
            return;
        }

        try {
            setIsLoading(true);
            await onScheduleDelete(scheduleId);
            toast.success("Dienstplan gelöscht");
            if (onRefresh) await onRefresh();
        } catch (error) {
            toast.error(error instanceof Error ? error.message : "Fehler beim Löschen des Dienstplans");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async (scheduleId: string) => {
        try {
            setSavingScheduleId(scheduleId);
            await onScheduleSave(scheduleId);
            toast.success("Dienstplan wurde in TimeOffice gespeichert");
        } catch (error) {
            toast.error(error instanceof Error ? error.message : "Fehler beim Speichern in TimeOffice");
            console.error(error);
        } finally {
            setSavingScheduleId(null);
        }
    };

    const startEditingDescription = (scheduleId: string, currentDescription?: string) => {
        setEditingDescriptionId(scheduleId);
        setEditingDescription(currentDescription || "");
    };

    const cancelEditingDescription = () => {
        setEditingDescriptionId(null);
        setEditingDescription("");
    };

    const saveDescription = async (scheduleId: string) => {
        if (!onDescriptionUpdate) return;

        try {
            setIsLoading(true);
            await onDescriptionUpdate(scheduleId, editingDescription);
            toast.success("Beschreibung aktualisiert");
            setEditingDescriptionId(null);
            setEditingDescription("");
            if (onRefresh) await onRefresh();
        } catch (error) {
            toast.error("Fehler beim Aktualisieren der Beschreibung");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (isoString: string) => {
        return new Date(isoString).toLocaleString("de-DE", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const getScheduleLabel = (description?: string) => {
        if (!description) return "Ohne Beschreibung";
        return description.length > 30 ? `${description.slice(0, 30)}...` : description;
    };

    if (schedulesMetadata.schedules.length === 0) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <p className="text-center text-muted-foreground">
                        Keine Dienstpläne verfügbar. Laden Sie einen Dienstplan hoch oder
                        generieren Sie einen neuen.
                    </p>
                </CardContent>
            </Card>
        );
    }

    // Sort schedules by generation date (newest first)
    const sortedSchedules = [...schedulesMetadata.schedules].sort(
        (a, b) => new Date(b.generatedAt).getTime() - new Date(a.generatedAt).getTime()
    );

    const handleCheckboxChange = (scheduleId: string, checked: boolean) => {
        const newSelection = checked
            ? [...selectedScheduleIds, scheduleId]
            : selectedScheduleIds.filter(id => id !== scheduleId);

        onMultipleSchedulesSelect?.(newSelection);
    };

    return (
        <div className="flex items-center gap-4">
            <div className="flex-1 ">
                {compareMode ? (
                    <div className="flex max-w-[720px] flex-wrap items-center gap-2">
                        <Badge variant="outline">
                            {schedulesMetadata.schedules.length} hochgeladen
                        </Badge>
                        <Badge variant="outline">
                            {selectedScheduleIds.length} zum Vergleich
                        </Badge>
                    </div>
                ) : (
                    <>
                        <Select
                            value={schedulesMetadata.selectedScheduleId || ""}
                            onValueChange={handleSelect}
                            disabled={isLoading}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Dienstplan auswählen..."/>
                            </SelectTrigger>
                            <SelectContent>
                                {sortedSchedules.map((schedule) => {
                                    return (
                                        <SelectItem key={schedule.scheduleId} value={schedule.scheduleId}>
                                            <div className="flex items-center gap-2">
                                                {schedule.isSelected && <CheckCircle className="h-4 w-4"/>}
                                                <span>
                          {getScheduleLabel(schedule.description)} - {formatDate(schedule.generatedAt)}
                        </span>
                                            </div>
                                        </SelectItem>
                                    );
                                })}
                            </SelectContent>
                        </Select>
                    </>
                )}
            </div>
            {!compareMode && schedulesMetadata.selectedScheduleId && (
                <div className="text-sm text-muted-foreground">
                    {(() => {
                        const selected = schedulesMetadata.schedules.find(
                            (s) => s.scheduleId === schedulesMetadata.selectedScheduleId
                        );
                        if (!selected) return null;
                        return (
                            <span>
                Aktuell: {getScheduleLabel(selected.description)} - {formatDate(selected.generatedAt)}
              </span>
                        );
                    })()}
                </div>
            )}
            <Dialog>
                <DialogTrigger asChild>
                    <Button variant="outline">
                        {compareMode ? "Vergleich verwalten" : `Alle Dienstpläne (${schedulesMetadata.schedules.length})`}
                    </Button>
                </DialogTrigger>
                <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-4xl">
                    <DialogHeader>
                        <DialogTitle>{compareMode ? "Dienstpläne zum Vergleich auswählen" : "Alle Dienstpläne"}</DialogTitle>
                        <DialogDescription>
                            {compareMode
                                ? "Wählen Sie mehrere Dienstpläne aus, um sie zu vergleichen."
                                : "Vergleichen Sie verschiedene generierte Dienstpläne."
                            }
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4">
                        {sortedSchedules.map((schedule, index) => {
                            const isChecked = selectedScheduleIds.includes(schedule.scheduleId);
                            return (
                                <Card
                                    key={schedule.scheduleId}
                                    className={
                                        compareMode && isChecked
                                            ? "border-primary border-2"
                                            : schedule.isSelected && !compareMode
                                                ? "border-primary border-2"
                                                : ""
                                    }
                                >
                                    <CardHeader>
                                        <div className="space-y-4">
                                            <div className="flex items-start gap-3 flex-1">
                                                {compareMode && (
                                                    <Checkbox
                                                        checked={isChecked}
                                                        onCheckedChange={(checked) => handleCheckboxChange(schedule.scheduleId, checked as boolean)}
                                                        className="mt-1"
                                                    />
                                                )}
                                                <div className="space-y-1 flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <CardTitle className="text-lg">
                                                            Dienstplan #{index + 1}
                                                        </CardTitle>
                                                        {schedule.isSelected && !compareMode && (
                                                            <Badge variant="default">Ausgewählt</Badge>
                                                        )}
                                                        {compareMode && isChecked && (
                                                            <Badge variant="default">Zum Vergleich</Badge>
                                                        )}
                                                    </div>
                                                    <div
                                                        className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                              <span className="flex items-center gap-1">
                                <Calendar className="h-4 w-4"/>
                                  {formatDate(schedule.generatedAt)}
                              </span>
                                                        {editingDescriptionId === schedule.scheduleId ? (
                                                            <div className="flex items-start gap-2 flex-1 mt-1">
                                                                <Textarea
                                                                    value={editingDescription}
                                                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditingDescription(e.target.value)}
                                                                    placeholder="Beschreibung hinzufügen..."
                                                                    className="text-sm min-h-[60px]"
                                                                    autoFocus
                                                                    maxLength={500}
                                                                    rows={2}
                                                                />
                                                                <div className="flex flex-col gap-1">
                                                                    <Button
                                                                        size="sm"
                                                                        variant="ghost"
                                                                        onClick={() => saveDescription(schedule.scheduleId)}
                                                                        disabled={isLoading}
                                                                        className="h-8"
                                                                    >
                                                                        <Check className="h-4 w-4"/>
                                                                    </Button>
                                                                    <Button
                                                                        size="sm"
                                                                        variant="ghost"
                                                                        onClick={cancelEditingDescription}
                                                                        disabled={isLoading}
                                                                        className="h-8 text-xs px-2"
                                                                    >
                                                                        ×
                                                                    </Button>
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <>
                                                                {schedule.description ? (
                                                                    <span className="flex items-start gap-2">
                                      <span
                                          className="whitespace-pre-wrap wrap-break-word">{schedule.description}</span>
                                                                        {!compareMode && onDescriptionUpdate && (
                                                                            <Button
                                                                                size="sm"
                                                                                variant="ghost"
                                                                                className="h-6 w-6 p-0 shrink-0"
                                                                                onClick={() => startEditingDescription(schedule.scheduleId, schedule.description)}
                                                                            >
                                                                                <Pencil className="h-3 w-3"/>
                                                                            </Button>
                                                                        )}
                                    </span>
                                                                ) : !compareMode && onDescriptionUpdate ? (
                                                                    <Button
                                                                        size="sm"
                                                                        variant="ghost"
                                                                        className="h-6 text-xs"
                                                                        onClick={() => startEditingDescription(schedule.scheduleId)}
                                                                    >
                                                                        <Pencil className="h-3 w-3 mr-1"/>
                                                                        Beschreibung hinzufügen
                                                                    </Button>
                                                                ) : null}
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            {!compareMode && (
                                                <div className="flex flex-wrap items-center justify-end gap-2 border-t pt-4">
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => handleSave(schedule.scheduleId)}
                                                        disabled={isLoading || savingScheduleId !== null}
                                                    >
                                                        {savingScheduleId === schedule.scheduleId ? (
                                                            <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
                                                        ) : (
                                                            <Save className="mr-2 h-4 w-4"/>
                                                        )}
                                                        In TimeOffice speichern
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant={schedule.isSelected ? "outline" : "default"}
                                                        onClick={() => handleSelect(schedule.scheduleId)}
                                                        disabled={isLoading || schedule.isSelected}
                                                    >
                                                        {isLoading ? (
                                                            <Loader2 className="h-4 w-4 animate-spin"/>
                                                        ) : schedule.isSelected ? (
                                                            "Aktiv"
                                                        ) : (
                                                            "Auswählen"
                                                        )}
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="destructive"
                                                        onClick={() => handleDelete(schedule.scheduleId)}
                                                        disabled={isLoading}
                                                    >
                                                        <Trash2 className="h-4 w-4"/>
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {schedule.comment && (
                                                <div className="text-sm text-muted-foreground italic">
                                                    {schedule.comment}
                                                </div>
                                            )}

                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <p className="font-semibold">Verstöße:</p>
                                                    <ul className="space-y-1 text-muted-foreground">
                                                        <li>
                                                            Vorwärtsrotation: {schedule.stats.forward_rotation_violations}
                                                        </li>
                                                        <li>
                                                            {">"}5 Tage am
                                                            Stück: {schedule.stats.consecutive_working_days_gt_5}
                                                        </li>
                                                        <li>Kein freies WE: {schedule.stats.no_free_weekend}</li>
                                                        <li>
                                                            {">"}3
                                                            Nachtschichten: {schedule.stats.consecutive_night_shifts_gt_3}
                                                        </li>
                                                    </ul>
                                                </div>
                                                <div>
                                                    <p className="font-semibold">Weitere Metriken:</p>
                                                    <ul className="space-y-1 text-muted-foreground">
                                                        <li>
                                                            Keine freien Tage um WE:{" "}
                                                            {schedule.stats.no_free_days_around_weekend}
                                                        </li>
                                                        <li>
                                                            Nicht frei nach Nachtschicht:{" "}
                                                            {schedule.stats.not_free_after_night_shift}
                                                        </li>
                                                        <li>
                                                            Verletzte Wünsche: {schedule.stats.violated_wish_total}
                                                        </li>
                                                        <li>
                                                            Überstunden: {schedule.stats.total_overtime_hours}h
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                </DialogContent>
            </Dialog>


        </div>
    );
}
