'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import {
    startSolveJob,
    importSolution,
    solverDelete,
    solverFetch,
    solverInsert,
    solverSolveMultiple,
} from '@/features/solver/solver.actions';
import type { SolverJob } from '@/entities/models/solver.model';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

export interface SolverExecOptions {
    caseId: number;
    caseIds?: number[];
    monthYear: string;
    start: string;
    end: string;
}

export interface ImportDialogParams {
    caseId: number;
    start: string;
    end: string;
    solutionType: string;
    solution: ScheduleSolutionRaw;
}

export interface MultipleImportDialogParams {
    caseId: number;
    start: string;
    end: string;
    solutionCount: number;
    feasibleSolutions?: number[];
    solutions: ScheduleSolutionRaw[];
}

export interface SolverOperationResult {
    succeeded: boolean;
}

interface UseSolverOperationsOptions {
    onAfterOperation?: () => Promise<void>;
    onSolveJobStarted?: (job: SolverJob) => void | Promise<void>;
    initialLastInsertedSolution?: ScheduleSolutionRaw | null;
    initialPendingInsertSolution?: ScheduleSolutionRaw | null;
}

export function useSolverOperations({ onAfterOperation, onSolveJobStarted, initialLastInsertedSolution, initialPendingInsertSolution }: UseSolverOperationsOptions = {}) {
    const [isExecuting, setIsExecuting] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const [progress, setProgress] = useState(0);
    const [executionStartTime, setExecutionStartTime] = useState<number | null>(null);
    const currentTimeoutMsRef = useRef<number>(60_000);

    // API-mode progress tracking
    const apiModeRef = useRef(false);
    const phase3StartMsRef = useRef<number | null>(null);
    const totalWeightsRef = useRef<number>(1);
    const weightIdRef = useRef<number>(0);
    const phase3TimeoutSecRef = useRef<number>(60);
    const currentSolveTimeoutRef = useRef<number>(60);

    const [phase, setPhase] = useState<string | null>(null);
    const [isIndeterminate, setIsIndeterminate] = useState(false);
    const [runLabel, setRunLabel] = useState<string | null>(null);

    const [showImportDialog, setShowImportDialog] = useState(false);
    const [importDialogParams, setImportDialogParams] = useState<ImportDialogParams | null>(null);

    const [showMultipleImportDialog, setShowMultipleImportDialog] = useState(false);
    const [multipleImportDialogParams, setMultipleImportDialogParams] = useState<MultipleImportDialogParams | null>(null);

    /**
     * Solution that is ready to be inserted into TimeOffice.
     * Set after a successful solve or after the user imports a solution to local storage.
     * Initialized from the server-selected schedule so insert always has a solution ready.
     * Passed to solverInsert when available; null falls back to CLI disk-read.
     */
    const [pendingInsertSolution, setPendingInsertSolution] = useState<ScheduleSolutionRaw | null>(
        initialPendingInsertSolution ?? null
    );

    /**
     * Solution that was last successfully inserted into TimeOffice.
     * Passed to solverDelete so the API can identify exactly which entries to remove.
     * Null falls back to CLI disk-read.
     * Initialized from server-persisted value so it survives page refreshes.
     */
    const [lastInsertedSolution, setLastInsertedSolution] = useState<ScheduleSolutionRaw | null>(
        initialLastInsertedSolution ?? null
    );

    // Single tick: handles CLI time-based progress OR smooth phase-3 fill in API mode
    useEffect(() => {
        if (!isExecuting || executionStartTime === null) {
            setProgress(0);
            return;
        }
        const interval = setInterval(() => {
            if (apiModeRef.current) {
                // API mode: only fill smoothly during phase_3_optimizing
                if (phase3StartMsRef.current !== null) {
                    const segmentSize = 100 / totalWeightsRef.current;
                    const completedProgress = weightIdRef.current * segmentSize;
                    const elapsed = Date.now() - phase3StartMsRef.current;
                    const timeoutMs = phase3TimeoutSecRef.current * 1000;
                    const fraction = Math.min(elapsed / timeoutMs, 0.98);
                    setProgress(completedProgress + segmentSize * (0.25 + fraction * 0.74));
                }
                // For phase_1 / phase_2: progress stays frozen (set by polling)
            } else {
                // CLI fallback: time-based linear fill
                const elapsed = Date.now() - executionStartTime;
                const timeoutMs = currentTimeoutMsRef.current;
                setProgress(Math.min((elapsed / timeoutMs) * 100, 99));
            }
        }, 100);
        return () => clearInterval(interval);
    }, [isExecuting, executionStartTime]);

    useEffect(() => {
        if (!isExecuting) {
            setProgress(0);
            setExecutionStartTime(null);
            setPhase(null);
            setIsIndeterminate(false);
            setRunLabel(null);
        }
    }, [isExecuting]);

    // API mode: poll GET /status while executing to get live phase info
    useEffect(() => {
        if (!isExecuting) return;
        let active = true;

        const poll = async () => {
            if (!active) return;
            // Direct browser fetch to the Route Handler — bypasses Server Action
            // session locking so this can run concurrently with the solve action.
            let raw: { isSolving?: boolean; is_solving?: boolean; phase?: string; weight_id?: number; total_weights?: number; timeout_set_for_phase_3?: number } | null = null;
            try {
                const res = await fetch('/api/solver/status', { cache: 'no-store' });
                if (res.ok) raw = await res.json();
            } catch { /* network error — skip tick */ }
            if (!active || !raw) return;
            // Map snake_case API response to camelCase
            const isSolving = raw.is_solving ?? raw.isSolving ?? false;
            if (!isSolving) return;
            const sp = {
                phase: raw.phase ?? 'idle',
                weightId: raw.weight_id,
                totalWeights: raw.total_weights,
                timeoutForPhase3: raw.timeout_set_for_phase_3,
            };
            apiModeRef.current = true;

            const totalWeights = sp.totalWeights ?? 1;
            const weightId = sp.weightId ?? 0;

            // Detect run change in solve-multiple
            if (weightIdRef.current !== weightId) {
                weightIdRef.current = weightId;
                phase3StartMsRef.current = null;
            }
            totalWeightsRef.current = totalWeights;
            phase3TimeoutSecRef.current =
                sp.timeoutForPhase3 && sp.timeoutForPhase3 > 0
                    ? sp.timeoutForPhase3
                    : currentSolveTimeoutRef.current;

            setRunLabel(totalWeights > 1 ? `Lauf ${weightId + 1}/${totalWeights}` : null);
            setPhase(sp.phase);

            const segmentSize = 100 / totalWeights;
            const completedProgress = weightId * segmentSize;

            if (sp.phase === 'phase_1_upper_bound') {
                setProgress(completedProgress + segmentSize * 0.02);
                setIsIndeterminate(true);
            } else if (sp.phase === 'phase_2_tight_bound') {
                setProgress(completedProgress + segmentSize * 0.12);
                setIsIndeterminate(true);
            } else if (sp.phase === 'phase_3_optimizing') {
                if (phase3StartMsRef.current === null) {
                    phase3StartMsRef.current = Date.now();
                }
                setIsIndeterminate(false);
                // Actual smooth fill is handled by the 100ms tick interval above
            }
        };

        const timeoutId = setTimeout(poll, 500);
        const intervalId = setInterval(poll, 2000);
        return () => {
            active = false;
            clearTimeout(timeoutId);
            clearInterval(intervalId);
        };
    }, [isExecuting]);

    const startExecution = (timeoutMs: number, solveTimeoutSec?: number) => {
        currentTimeoutMsRef.current = timeoutMs;
        currentSolveTimeoutRef.current = solveTimeoutSec ?? 60;
        apiModeRef.current = false;
        phase3StartMsRef.current = null;
        totalWeightsRef.current = 1;
        weightIdRef.current = 0;
        phase3TimeoutSecRef.current = solveTimeoutSec ?? 60;
        setPhase(null);
        setIsIndeterminate(false);
        setRunLabel(null);
        setExecutionStartTime(Date.now());
        setProgress(0);
        setIsExecuting(true);
    };

    const finishExecution = async () => {
        setIsExecuting(false);
        await onAfterOperation?.();
    };

    const getSelectedUnits = (opts: SolverExecOptions) =>
        opts.caseIds && opts.caseIds.length > 0 ? opts.caseIds : [opts.caseId];

    async function executeFetch(opts: SolverExecOptions, skipFinish: boolean = false): Promise<SolverOperationResult> {
        if (!skipFinish) startExecution(60_000);
        const unit = getSelectedUnits(opts);
        try {
            const result = await solverFetch(opts.caseId, opts.monthYear, {
                unit,
                start: opts.start,
                end: opts.end,
            });
            if (!result.success) {
                toast.error(result.error);
                return { succeeded: false };
            }
            if (result.data.job.status === 'completed') {
                toast.success('Daten erfolgreich von der Datenbank abgerufen');
                return { succeeded: true };
            }
            toast.error('Fehler beim Abrufen der Daten', { description: result.data.job.error ?? result.data.job.consoleOutput });
            return { succeeded: false };
        } finally {
            if (!skipFinish) await finishExecution();
        }
    }

    async function executeSolve(opts: SolverExecOptions, timeout: number, skipFinish: boolean = false): Promise<SolverOperationResult> {
        if (!skipFinish) {
            startExecution(timeout * 1_000 + 10_000, timeout);
        }
        const unit = getSelectedUnits(opts);
        try {
            const result = await startSolveJob(opts.caseId, {
                unit,
                start: opts.start,
                end: opts.end,
                timeout,
            });
            if (!result.success) {
                toast.error(result.error);
                return { succeeded: false };
            }
            await onSolveJobStarted?.(result.data.job);
            if (!skipFinish) {
                toast.success('Solve-Job gestartet');
            }
            return { succeeded: true };
        } finally {
            if (!skipFinish) {
                setIsExecuting(false);
            }
        }
    }

    async function executeSolveMultiple(opts: SolverExecOptions, timeout: number, skipFinish: boolean = false): Promise<SolverOperationResult> {
        if (!skipFinish) startExecution(timeout * 3 * 1_000 + 20_000, timeout);
        const unit = getSelectedUnits(opts);
        try {
            const result = await solverSolveMultiple(opts.caseId, opts.monthYear, {
                unit,
                start: opts.start,
                end: opts.end,
                timeout,
            });
            if (!result.success) {
                toast.error(result.error);
                return { succeeded: false };
            }
            if (result.data.job.status === 'completed') {
                const successCount = result.data.scheduleInfo.solutionsGenerated;
                const expectedCount = 3;
                if (successCount === expectedCount) {
                    toast.success(`${successCount} Dienstpläne erfolgreich erstellt`, {
                        description: 'Alle Lösungen können nun importiert werden',
                    });
                } else if (successCount > 0) {
                    toast.warning(`Nur ${successCount} von ${expectedCount} Dienstplänen erstellt`, {
                        description: 'Einige Lösungen konnten nicht generiert werden (kein FEASIBLE Status)',
                    });
                } else {
                    toast.error('Keine Dienstpläne erstellt', {
                        description: 'Der Solver konnte keine FEASIBLE Lösungen finden',
                    });
                }
                if (successCount > 0) {
                    setMultipleImportDialogParams({
                        caseId: opts.caseId,
                        start: opts.start,
                        end: opts.end,
                        solutionCount: successCount,
                        feasibleSolutions: result.data.scheduleInfo.feasibleSolutions,
                        solutions: result.data.solutions,
                    });
                    setShowMultipleImportDialog(true);
                }
                return { succeeded: successCount > 0 };
            }
            toast.error('Fehler beim Erstellen mehrerer Dienstpläne', { description: result.data.job.error ?? result.data.job.consoleOutput });
            return { succeeded: false };
        } finally {
            if (!skipFinish) await finishExecution();
        }
    }

    async function executeInsert(opts: SolverExecOptions, skipFinish: boolean = false): Promise<SolverOperationResult> {
        if (!skipFinish) startExecution(60_000);
        const unit = getSelectedUnits(opts);
        try {
            const result = await solverInsert(opts.caseId, opts.monthYear, {
                unit,
                start: opts.start,
                end: opts.end,
            }, pendingInsertSolution ?? undefined);
            if (!result.success) {
                toast.error(result.error);
                return { succeeded: false };
            }
            if (result.data.job.status === 'completed') {
                toast.success('Daten erfolgreich in die Datenbank eingefügt');
                setLastInsertedSolution(pendingInsertSolution);
                return { succeeded: true };
            }
            toast.error('Fehler beim Einfügen der Daten', { description: result.data.job.error ?? result.data.job.consoleOutput });
            return { succeeded: false };
        } finally {
            if (!skipFinish) await finishExecution();
        }
    }

    async function executeDelete(opts: SolverExecOptions, skipFinish: boolean = false): Promise<SolverOperationResult> {
        if (!skipFinish) startExecution(60_000);
        const unit = getSelectedUnits(opts);
        try {
            const result = await solverDelete(opts.caseId, opts.monthYear, {
                unit,
                start: opts.start,
                end: opts.end,
            }, lastInsertedSolution ?? undefined);
            if (!result.success) {
                toast.error(result.error);
                return { succeeded: false };
            }
            if (result.data.job.status === 'completed') {
                toast.success('Daten erfolgreich aus der Datenbank gelöscht');
                setLastInsertedSolution(null);
                return { succeeded: true };
            }
            toast.error('Fehler beim Löschen der Daten', { description: result.data.job.error ?? result.data.job.consoleOutput });
            return { succeeded: false };
        } finally {
            if (!skipFinish) await finishExecution();
        }
    }

    async function handleImport(
        caseId: number,
        monthYear: string,
        params: { start: string; end: string; solutionType: string; solution: ScheduleSolutionRaw },
    ): Promise<void> {
        setIsImporting(true);
        try {
            const result = await importSolution(caseId, monthYear, params);
            if (!result.success) {
                toast.error(result.error);
            } else {
                toast.success('Lösung erfolgreich importiert');
                // The imported solution becomes the candidate for the next insert into TimeOffice
                setPendingInsertSolution(params.solution);
            }
        } finally {
            setIsImporting(false);
        }
    }

    return {
        isExecuting,
        isImporting,
        progress,
        phase,
        isIndeterminate,
        runLabel,
        executionStartTime,
        showImportDialog,
        setShowImportDialog,
        importDialogParams,
        showMultipleImportDialog,
        setShowMultipleImportDialog,
        multipleImportDialogParams,
        pendingInsertSolution,
        lastInsertedSolution,
        executeFetch,
        executeSolve,
        executeSolveMultiple,
        executeInsert,
        executeDelete,
        handleImport,
    };
}
