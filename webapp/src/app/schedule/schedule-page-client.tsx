"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { Card } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CalendarDays, Maximize2, Upload } from "lucide-react";
import { ScheduleTable } from "@/features/schedule/components/schedule-table";
import { StatsGrid } from "@/features/schedule/components/stats-grid";
import { ScheduleFileUpload } from "@/features/schedule/components/schedule-file-upload";
import { cn } from "@/lib/utils";
import { ScheduleLegend } from "@/features/schedule/components/schedule-legend";
import { ScheduleSelector } from "@/components/schedule-selector";
import { DescriptionInputDialog } from "@/components/description-input-dialog";
import {
  deleteScheduleAction,
  getScheduleByIdAction,
  saveScheduleAction,
  selectScheduleAction,
  updateScheduleMetadataAction,
  writeScheduleToTimeOfficeAction,
} from "@/features/schedule/schedule.actions";
import { SchedulesMetadata, ScheduleSolution, ScheduleSolutionRaw } from "@/entities/models/schedule.model";
import { parseSolutionFile } from "@/lib/services/schedule-parser";
import { toast } from "sonner";
import { Root as Switch, Thumb as SwitchThumb } from "@radix-ui/react-switch";
import { useRouter } from "next/navigation";

interface SchedulePageClientProps {
  caseId: number;
  monthYear: string;
  initialSchedule: ScheduleSolution | null;
  initialMetadata: SchedulesMetadata;
}

export function SchedulePageClient({ caseId, monthYear, initialSchedule, initialMetadata }: SchedulePageClientProps) {
  const router = useRouter();
  const schedule = initialSchedule;
  const schedulesMetadata = initialMetadata;

  const [reducedView, setReducedView] = useState(false);
  const [isSaving, startSaveTransition] = useTransition();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showDescriptionDialog, setShowDescriptionDialog] = useState(false);
  const [pendingSolution, setPendingSolution] = useState<ScheduleSolutionRaw | null>(null);
  const tableRef = useRef<HTMLDivElement>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedScheduleIds, setSelectedScheduleIds] = useState<string[]>([]);
  const [multipleSchedules, setMultipleSchedules] = useState<
    (ScheduleSolution & { scheduleId: string; description?: string })[]
  >([]);
  const [isMultipleSchedulesLoading, setIsMultipleSchedulesLoading] = useState(false);

  // Fetch multiple schedules when compare mode IDs change
  useEffect(() => {
    if (selectedScheduleIds.length === 0) {
      setMultipleSchedules([]);
      return;
    }

    let cancelled = false;
    setIsMultipleSchedulesLoading(true);

    (async () => {
      try {
        const results = await Promise.all(
          selectedScheduleIds.map(async (scheduleId) => {
            const data = await getScheduleByIdAction(caseId, monthYear, scheduleId);
            if (!data.solution) return null;
            const parsedSolution = parseSolutionFile(data.solution);
            return { ...parsedSolution, scheduleId, description: data.description };
          }),
        );
        if (!cancelled) {
          setMultipleSchedules(results.filter((s): s is NonNullable<typeof s> => s !== null));
        }
      } finally {
        if (!cancelled) setIsMultipleSchedulesLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedScheduleIds, caseId, monthYear]);

  const handleFileLoaded = async (solutionData: ScheduleSolutionRaw) => {
    setPendingSolution(solutionData);
    setShowDescriptionDialog(true);
  };

  const handleDescriptionConfirm = async (description?: string) => {
    if (!pendingSolution) return;

    startSaveTransition(async () => {
      const scheduleId = Date.now().toString();
      const result = await saveScheduleAction(caseId, monthYear, scheduleId, pendingSolution, description, true);
      if (!result.success) {
        toast.error(result.error || "Fehler beim Speichern des Dienstplans");
        return;
      }
      setShowDescriptionDialog(false);
      setPendingSolution(null);
      toast.success("Dienstplan erfolgreich geladen");
    });
  };

  const handleScheduleSelect = async (scheduleId: string) => {
    const result = await selectScheduleAction(caseId, monthYear, scheduleId);
    if (!result.success) {
      toast.error(result.error || "Fehler beim Auswählen des Dienstplans");
    }
  };

  const handleScheduleDelete = async (scheduleId: string) => {
    const result = await deleteScheduleAction(caseId, monthYear, scheduleId);
    if (!result.success) {
      throw new Error(result.error || "Fehler beim Löschen des Dienstplans");
    }
    router.refresh();
  };

  const handleScheduleWrite = async (scheduleId: string) => {
    const result = await writeScheduleToTimeOfficeAction(caseId, monthYear, scheduleId);
    if (!result.success) {
      throw new Error(result.error || "Dienstplan konnte nicht in TimeOffice gespeichert werden.");
    }
  };

  const handleDescriptionUpdate = async (scheduleId: string, description: string) => {
    const result = await updateScheduleMetadataAction(caseId, monthYear, scheduleId, { description });
    if (!result.success) {
      toast.error(result.error || "Fehler beim Aktualisieren der Beschreibung");
    }
  };

  const handleMultipleSchedulesSelect = (scheduleIds: string[]) => {
    setSelectedScheduleIds(scheduleIds);
  };

  const toggleCompareMode = () => {
    if (compareMode) {
      setSelectedScheduleIds([]);
    }
    setCompareMode(!compareMode);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement && tableRef.current) {
      tableRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen changes (e.g., ESC key)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  return (
    <div className="py-6 space-y-6">
      {/* Header */}
      <header className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Dienstplan</h1>
            <p className="text-muted-foreground">Analysiere und visualisiere Mitarbeiter-Schichtpläne</p>
          </div>
          {schedule && (
            <Badge variant="outline" className="gap-2">
              <CalendarDays className="h-4 w-4" />
              {schedule.days.length} Tage
            </Badge>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4">
          {!compareMode && <ScheduleFileUpload onFileLoaded={handleFileLoaded} isLoading={isSaving} />}

          {/* Schedule Selector */}
          {schedulesMetadata && (
            <ScheduleSelector
              schedulesMetadata={schedulesMetadata}
              onScheduleSelect={handleScheduleSelect}
              onScheduleDelete={handleScheduleDelete}
              onScheduleSave={handleScheduleWrite}
              compareMode={compareMode}
              selectedScheduleIds={selectedScheduleIds}
              onMultipleSchedulesSelect={handleMultipleSchedulesSelect}
              onDescriptionUpdate={handleDescriptionUpdate}
            />
          )}

          {schedulesMetadata && schedulesMetadata.schedules.length >= 2 && (
            <Button onClick={toggleCompareMode} variant={compareMode ? "default" : "outline"} className="gap-2">
              {compareMode ? "Vergleich beenden" : "Dienstpläne vergleichen"}
            </Button>
          )}

          <div
            role="button"
            tabIndex={0}
            className={cn(
              buttonVariants({
                variant: "outline",
                size: "default",
              }),
              "inline-flex items-center gap-2",
            )}
            onClick={() => setReducedView(!reducedView)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setReducedView(!reducedView);
              }
            }}
            aria-pressed={reducedView}
          >
            <Switch
              id="reduced-view-toggle"
              checked={reducedView}
              className={
                "relative inline-flex h-6 w-11 items-center rounded-full p-1 bg-muted/90 data-[state=checked]:bg-primary pointer-events-auto cursor-pointer mr-2"
              }
            >
              <SwitchThumb
                className={
                  "block h-4 w-4 rounded-full bg-card shadow transform transition-transform data-[state=checked]:translate-x-5 pointer-events-auto"
                }
              />
            </Switch>
            <span className="text-sm ml-2 select-none pointer-events-auto cursor-pointer" role="button">
              Reduzierte Ansicht
            </span>
          </div>

          <Button onClick={toggleFullscreen} variant="outline" className="gap-2">
            <Maximize2 className="h-4 w-4" />
            {isFullscreen ? "Exit" : "Enter"} Fullscreen
          </Button>
        </div>
      </header>

      {compareMode && isMultipleSchedulesLoading ? (
        <Card className="border-border/50 p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="text-lg text-muted-foreground">Lädt...</div>
          </div>
        </Card>
      ) : compareMode && multipleSchedules && multipleSchedules.length > 0 ? (
        <>
          {/* Schedule Table in Compare Mode */}
          <Card
            ref={tableRef}
            className={cn(
              "overflow-hidden border-border/50 shadow-lg relative",
              isFullscreen && "h-screen bg-background flex flex-col p-4 rounded-none border-0",
            )}
          >
            {isFullscreen && (
              <Button onClick={toggleFullscreen} variant="outline" className="absolute top-4 right-4 z-50 gap-2">
                <Maximize2 className="h-4 w-4" />
                Exit Fullscreen
              </Button>
            )}
            <ScheduleTable
              schedules={multipleSchedules}
              compareMode={true}
              isFullscreen={isFullscreen}
              reducedView={reducedView}
            />
          </Card>

          {/* Legend */}
          <ScheduleLegend />
        </>
      ) : schedule && !compareMode ? (
        <>
          {/* Statistics Grid */}
          <StatsGrid stats={schedule.stats} />

          {/* Schedule Table */}
          <Card
            ref={tableRef}
            className={cn(
              "overflow-hidden border-border/50 shadow-lg relative",
              isFullscreen && "h-screen bg-background flex flex-col p-4 rounded-none border-0",
            )}
          >
            {isFullscreen && (
              <Button onClick={toggleFullscreen} variant="outline" className="absolute top-4 right-4 z-50 gap-2">
                <Maximize2 className="h-4 w-4" />
                Exit Fullscreen
              </Button>
            )}
            <ScheduleTable
              employees={schedule.employees}
              days={schedule.days}
              shifts={schedule.shifts}
              variables={schedule.variables}
              fulfilledDayOffCells={schedule.fulfilledDayOffCells}
              fulfilledShiftWishCells={schedule.fulfilledShiftWishCells}
              allDayOffWishCells={schedule.allDayOffWishCells}
              allShiftWishColors={schedule.allShiftWishColors}
              isFullscreen={isFullscreen}
              reducedView={reducedView}
            />
          </Card>

          {/* Legend */}
          <ScheduleLegend />
        </>
      ) : compareMode ? (
        <Card className="border-border/50 p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="rounded-full bg-muted p-6">
              <CalendarDays className="h-12 w-12 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">Keine Dienstpläne ausgewählt</h3>
              <p className="text-muted-foreground max-w-md">
                Wähle in Vergleich verwalten mindestens einen hochgeladenen Dienstplan aus.
              </p>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="border-border/50 p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="rounded-full bg-muted p-6">
              <Upload className="h-12 w-12 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">Kein Dienstplan geladen</h3>
              <p className="text-muted-foreground max-w-md">
                Lade eine solution.json Datei hoch, um die Dienstplan-Analyse und Visualisierungen anzuzeigen.
              </p>
            </div>
            <Button onClick={() => document.getElementById("file-upload")?.click()} className="gap-2">
              <Upload className="h-4 w-4" />
              Solution-Datei hochladen
            </Button>
          </div>
        </Card>
      )}

      {/* Description Input Dialog */}
      <DescriptionInputDialog
        open={showDescriptionDialog}
        onOpenChange={setShowDescriptionDialog}
        onConfirm={handleDescriptionConfirm}
        isLoading={isSaving}
      />
    </div>
  );
}
