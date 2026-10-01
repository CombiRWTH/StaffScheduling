"use client";

import React, { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { parseMonthYear } from "@/lib/utils/case-utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SolverProgressDisplay } from "@/features/solver/components/solver-progress-display";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, CheckCircle2, Database, Info, Loader2, Play, Trash2, Upload } from "lucide-react";
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
import type { SolverExecOptions } from "@/features/solver/hooks/use-solver-operations";
import { useSolverOperations } from "@/features/solver/hooks/use-solver-operations";
import { SolverCommandType, SolverJob } from "@/entities/models/solver.model";
import { ImportSolutionDialog } from "@/components/import-solution-dialog";
import { ImportMultipleSolutionsDialog } from "@/components/import-multiple-solutions-dialog";

interface SolverControlPanelProps {
  caseId: number;
  selectedCaseIds?: number[];
  monthYear: string;
  onAfterOperation?: () => Promise<void>;
  onSolveJobStarted?: (job: SolverJob) => void | Promise<void>;
  initialLastInsertedSolution?: import("@/entities/models/schedule.model").ScheduleSolutionRaw | null;
  initialPendingInsertSolution?: import("@/entities/models/schedule.model").ScheduleSolutionRaw | null;
}

export function SolverControlPanel({
  caseId,
  selectedCaseIds = [],
  monthYear,
  onAfterOperation,
  onSolveJobStarted,
  initialLastInsertedSolution,
  initialPendingInsertSolution,
}: SolverControlPanelProps) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const [command, setCommand] = useState<SolverCommandType>("solve");
  const [solveTimeout, setSolveTimeout] = useState("60");

  const [showDeleteMissingDialog, setShowDeleteMissingDialog] = useState(false);
  const [showDeleteConfirmDialog, setShowDeleteConfirmDialog] = useState(false);
  const [showInsertMissingDialog, setShowInsertMissingDialog] = useState(false);

  // queue for deferred execution when user confirms via dialog
  const [queuedOpts, setQueuedOpts] = useState<SolverExecOptions | null>(null);
  const [queuedCmd, setQueuedCmd] = useState<SolverCommandType | null>(null);

  const performQueued = async () => {
    if (!queuedCmd || !queuedOpts) return;
    const opts = queuedOpts;
    setQueuedCmd(null);
    setQueuedOpts(null);
    if (queuedCmd === "delete") {
      await executeDelete(opts);
    } else if (queuedCmd === "insert") {
      await executeInsert(opts);
    }
  };

  // Month and year state
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);

  // Set default month and year from URL params
  React.useEffect(() => {
    if (caseId && monthYear && selectedMonth === null && selectedYear === null) {
      const { month, year } = parseMonthYear(monthYear);
      setSelectedMonth(month);
      setSelectedYear(year);
    }
  }, [caseId, monthYear, selectedMonth, selectedYear]);

  const {
    isExecuting,
    isImporting,
    progress,
    phase,
    isIndeterminate,
    runLabel,
    showImportDialog,
    setShowImportDialog,
    importDialogParams,
    showMultipleImportDialog,
    setShowMultipleImportDialog,
    multipleImportDialogParams,
    executeFetch,
    executeSolve,
    executeSolveMultiple,
    executeInsert,
    executeDelete,
    handleImport,
    pendingInsertSolution,
    lastInsertedSolution,
  } = useSolverOperations({
    onAfterOperation,
    onSolveJobStarted,
    initialLastInsertedSolution: initialLastInsertedSolution ?? null,
    initialPendingInsertSolution: initialPendingInsertSolution ?? null,
  });

  const buildExecutionOptions = (targetCaseIds: number[]) => {
    if (selectedMonth === null || selectedYear === null) {
      return null;
    }

    const firstDay = new Date(selectedYear, selectedMonth - 1, 1);
    const lastDay = new Date(selectedYear, selectedMonth, 0);

    const start =
      firstDay.getFullYear() +
      "-" +
      String(firstDay.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(firstDay.getDate()).padStart(2, "0");

    const end =
      lastDay.getFullYear() +
      "-" +
      String(lastDay.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(lastDay.getDate()).padStart(2, "0");

    return {
      caseId: targetCaseIds[0],
      caseIds: targetCaseIds,
      monthYear,
      start,
      end,
    };
  };

  const handleExecute = async () => {
    if (!caseId) return;

    if (selectedMonth === null || selectedYear === null) return;
    const targetCaseIds = selectedCaseIds.length > 0 ? selectedCaseIds : [caseId];
    const execOpts = buildExecutionOptions(targetCaseIds);

    if (!execOpts) return;

    let fetchSucceeded = false;

    switch (command) {
      case "fetch": {
        const result = await executeFetch(execOpts);
        fetchSucceeded = result.succeeded;
        break;
      }
      case "solve":
        await executeSolve(execOpts, parseInt(solveTimeout, 10));
        break;
      case "solve-multiple":
        await executeSolveMultiple(execOpts, parseInt(solveTimeout, 10));
        break;
      case "insert":
        if (!pendingInsertSolution) {
          setQueuedCmd("insert");
          setQueuedOpts(execOpts);
          setShowInsertMissingDialog(true);
          return;
        }
        await executeInsert(execOpts);
        break;
      case "delete": {
        if (!lastInsertedSolution) {
          setQueuedCmd("delete");
          setQueuedOpts(execOpts);
          setShowDeleteMissingDialog(true);
          return;
        }
        // ask for final confirmation too
        setQueuedCmd("delete");
        setQueuedOpts(execOpts);
        setShowDeleteConfirmDialog(true);
        return;
      }
    }

    // After fetch, keep the first selected case active while preserving the multi-case selection in the URL.
    if (command === "fetch" && fetchSucceeded && selectedMonth !== null && selectedYear !== null) {
      const monthStr = String(selectedMonth).padStart(2, "0");
      const newMonthYear = `${monthStr}_${selectedYear}`;
      const params = new URLSearchParams(searchParams.toString());
      params.set("caseId", String(targetCaseIds[0]));
      params.set("caseIds", targetCaseIds.join(","));
      params.set("monthYear", newMonthYear);
      router.push(`${pathname}?${params.toString()}`);
    }
  };

  const getCommandIcon = (cmd: SolverCommandType) => {
    switch (cmd) {
      case "fetch":
        return <Database className="h-4 w-4" />;
      case "solve":
      case "solve-multiple":
        return <Play className="h-4 w-4" />;
      case "insert":
        return <Upload className="h-4 w-4" />;
      case "delete":
        return <Trash2 className="h-4 w-4" />;
      default:
        return <Play className="h-4 w-4" />;
    }
  };

  const getCommandDescription = (cmd: SolverCommandType) => {
    switch (cmd) {
      case "fetch":
        return "Ruft Daten aus der Datenbank ab und schreibt JSON-Dateien";
      case "solve":
        return "Löst das Planungsproblem für eine einzelne Lösung";
      case "solve-multiple":
        return "Generiert mehrere Lösungen für das Planungsproblem";
      case "insert":
        return "Fügt Daten aus JSON-Dateien in die Datenbank ein";
      case "delete":
        return "Löscht Daten aus der Datenbank (Reset)";
      default:
        return "";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Solver steuern</CardTitle>
        <CardDescription>
          {selectedCaseIds.length > 0
            ? `Ausgewählte Fälle: ${selectedCaseIds.join(", ")}`
            : caseId
              ? `Ausgewählter Fall: ${caseId}`
              : "Bitte wählen Sie einen Fall aus"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Command Selection */}
        <div className="space-y-2">
          <Label htmlFor="command">Befehl</Label>
          <Select value={command} onValueChange={(v) => setCommand(v as SolverCommandType)}>
            <SelectTrigger id="command">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {/* Restore when POST /fetch is registered in the backend.
                            <SelectItem value="fetch">
                                <div className="flex items-center gap-2">
                                    <Database className="h-4 w-4"/>
                                    <span>Daten abrufen (fetch)</span>
                                </div>
                            </SelectItem>
                            */}
              <SelectItem value="solve">
                <div className="flex items-center gap-2">
                  <Play className="h-4 w-4" />
                  <span>Lösen (solve)</span>
                </div>
              </SelectItem>
              {/* Restore when POST /solve-multiple, /insert and /delete are registered.
                            <SelectItem value="solve-multiple">
                                <div className="flex items-center gap-2">
                                    <Play className="h-4 w-4"/>
                                    <span>Mehrfach lösen (solve-multiple)</span>
                                </div>
                            </SelectItem>
                            <SelectItem value="insert">
                                <div className="flex items-center gap-2">
                                    <Upload className="h-4 w-4"/>
                                    <span>Einfügen (insert)</span>
                                </div>
                            </SelectItem>
                            <SelectItem value="delete">
                                <div className="flex items-center gap-2">
                                    <Trash2 className="h-4 w-4"/>
                                    <span>Löschen (delete)</span>
                                </div>
                            </SelectItem>
                            */}
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">{getCommandDescription(command)}</p>
          {command === "insert" && (
            <div
              className={`flex items-center gap-1.5 text-xs mt-1 ${pendingInsertSolution ? "text-green-600" : "text-muted-foreground"}`}
            >
              {pendingInsertSolution ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Lösung bereit für Einspielung
                </>
              ) : (
                <>
                  <Info className="h-3.5 w-3.5" />
                  Keine Lösung im Speicher – API liest von Disk (nur CLI)
                </>
              )}
            </div>
          )}
          {command === "delete" && (
            <div
              className={`flex items-center gap-1.5 text-xs mt-1 ${lastInsertedSolution ? "text-amber-600" : "text-muted-foreground"}`}
            >
              {lastInsertedSolution ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Letzte eingespielten Lösung vorhanden – wird direkt übergeben
                </>
              ) : (
                <>
                  <Info className="h-3.5 w-3.5" />
                  Keine eingespielnte Lösung im Speicher – API/CLI liest von Disk
                </>
              )}
            </div>
          )}
        </div>

        {/* Month and Year Selection */}
        {/*
                <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="month">Monat</Label>
                            <Select
                                value={selectedMonth?.toString() || ''}
                                onValueChange={(v) => setSelectedMonth(parseInt(v))}
                                disabled={isLocked}
                            >
                                <SelectTrigger id="month">
                                    <SelectValue placeholder="Monat wählen"/>
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="1">Januar</SelectItem>
                                    <SelectItem value="2">Februar</SelectItem>
                                    <SelectItem value="3">März</SelectItem>
                                    <SelectItem value="4">April</SelectItem>
                                    <SelectItem value="5">Mai</SelectItem>
                                    <SelectItem value="6">Juni</SelectItem>
                                    <SelectItem value="7">Juli</SelectItem>
                                    <SelectItem value="8">August</SelectItem>
                                    <SelectItem value="9">September</SelectItem>
                                    <SelectItem value="10">Oktober</SelectItem>
                                    <SelectItem value="11">November</SelectItem>
                                    <SelectItem value="12">Dezember</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="year">Jahr</Label>
                            <Select
                                value={selectedYear?.toString() || ''}
                                onValueChange={(v) => setSelectedYear(parseInt(v))}
                                disabled={isLocked}
                            >
                                <SelectTrigger id="year">
                                    <SelectValue placeholder="Jahr wählen"/>
                                </SelectTrigger>
                                <SelectContent>
                                    {Array.from({length: 15}, (_, i) => new Date().getFullYear() - 5 + i).map((year) => (
                                        <SelectItem key={year} value={year.toString()}>
                                            {year}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                */}
        {(command === "solve" || command === "solve-multiple") && (
          <div className="space-y-2">
            <Label htmlFor="timeout">Timeout (Sekunden)</Label>
            <Input
              id="timeout"
              type="number"
              min="1"
              value={solveTimeout}
              onChange={(e) => setSolveTimeout(e.target.value)}
              disabled={isExecuting}
            />
          </div>
        )}

        {/* Execute Button */}
        <Button
          onClick={handleExecute}
          disabled={!caseId || selectedMonth === null || selectedYear === null || isExecuting}
          className="w-full"
          size="lg"
          variant={command === "delete" ? "destructive" : "default"}
        >
          {isExecuting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Wird ausgeführt...
            </>
          ) : (
            <>
              {getCommandIcon(command)}
              <span className="ml-2">Ausführen</span>
            </>
          )}
        </Button>

        {isExecuting && (
          <SolverProgressDisplay
            progress={progress}
            phase={phase}
            isIndeterminate={isIndeterminate}
            runLabel={runLabel}
            command={command}
            timeout={parseInt(solveTimeout, 10)}
          />
        )}
      </CardContent>

      {/* Import solution dialog */}
      {importDialogParams && (
        <ImportSolutionDialog
          open={showImportDialog}
          onOpenChange={setShowImportDialog}
          caseId={importDialogParams.caseId}
          start={importDialogParams.start}
          end={importDialogParams.end}
          solutionType={importDialogParams.solutionType}
          onImport={(params) =>
            handleImport(caseId, monthYear, {
              ...params,
              solution: importDialogParams.solution,
            })
          }
          isImporting={isImporting}
        />
      )}

      {/* Import multiple solutions dialog */}
      {multipleImportDialogParams && (
        <ImportMultipleSolutionsDialog
          open={showMultipleImportDialog}
          onOpenChange={setShowMultipleImportDialog}
          caseId={multipleImportDialogParams.caseId}
          start={multipleImportDialogParams.start}
          end={multipleImportDialogParams.end}
          solutionCount={multipleImportDialogParams.solutionCount}
          feasibleSolutions={multipleImportDialogParams.feasibleSolutions}
          onImport={(params) =>
            handleImport(caseId, monthYear, {
              ...params,
              solution: multipleImportDialogParams.solutions[params.solutionIndex ?? 0],
            })
          }
          isImporting={isImporting}
        />
      )}

      {/* Confirmation dialogs */}
      <AlertDialog open={showDeleteMissingDialog} onOpenChange={setShowDeleteMissingDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Löschung ohne eingespielten Plan
            </AlertDialogTitle>
            <AlertDialogDescription>
              Es existiert kein zuletzt eingespielter Dienstplan im Speicher. Der Löschvorgang greift auf die Festplatte
              zurück.
              <br />
              <br />
              Fortfahren?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                setShowDeleteMissingDialog(false);
                await performQueued();
              }}
            >
              Fortfahren
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showDeleteConfirmDialog} onOpenChange={setShowDeleteConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Dienstplan wirklich löschen?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Die ausgewählten Daten werden aus der Datenbank entfernt. Dies kann nicht rückgängig gemacht werden.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                setShowDeleteConfirmDialog(false);
                await performQueued();
              }}
            >
              Fortfahren
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showInsertMissingDialog} onOpenChange={setShowInsertMissingDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Export ohne Plan im Speicher
            </AlertDialogTitle>
            <AlertDialogDescription>
              Es befindet sich kein Dienstplan im Speicher. Beim Export werden die Daten von der Festplatte gelesen.
              <br />
              <br />
              Fortfahren?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                setShowInsertMissingDialog(false);
                await performQueued();
              }}
            >
              Fortfahren
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
