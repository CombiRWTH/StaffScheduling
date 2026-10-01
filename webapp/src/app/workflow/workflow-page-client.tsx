'use client';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouter} from 'next/navigation';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {SolverProgressDisplay} from '@/features/solver/components/solver-progress-display';
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
    AlertCircle,
    AlertTriangle,
    Calendar,
    CheckCircle2,
    Download,
    Edit,
    FolderOpen,
    Info,
    Loader2,
    Play,
    PlayCircle,
    Trash2,
    Upload,
} from 'lucide-react';
import {ImportSolutionDialog} from '@/components/import-solution-dialog';
import {ImportMultipleSolutionsDialog} from '@/components/import-multiple-solutions-dialog';
import {TimeoutConfigDialog} from '@/components/timeout-config-dialog';
import {JobHistoryTable} from '@/features/solver/components/job-history-table';
import {checkSolveJob} from '@/features/solver/solver.actions';
import {
    getSolveJobHistoryKey,
    readSolveJobHistory,
    writeSolveJobHistory,
} from '@/features/solver/solve-job-history-storage';
import {useSolverOperations} from '@/features/solver/hooks/use-solver-operations';

import type { SolveParams, SolverJob } from '@/entities/models/solver.model';
import type { SolverHealthResult } from '@/application/ports/solver.service';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

type WorkflowAction = 'delete' | 'fetch' | 'solve' | 'multi-solve' | 'insert' | 'edit-wishes';

interface ActionState {
    status: 'idle' | 'running' | 'success' | 'error';
    message?: string;
}

interface WorkflowPageClientProps {
    caseId: number;
    monthYear: string;
    startDate: string;
    endDate: string;
    isoStart: string;
    isoEnd: string;
    initialConfig: SolverHealthResult | null;
    initialJobs: SolverJob[];
    initialLastInsertedSolution: ScheduleSolutionRaw | null;
    initialPendingInsertSolution: ScheduleSolutionRaw | null;
}

export function WorkflowPageClient({
    caseId,
    monthYear,
    startDate,
    endDate,
    isoStart,
    isoEnd,
    initialConfig,
    initialJobs,
    initialLastInsertedSolution,
    initialPendingInsertSolution,
}: WorkflowPageClientProps) {
    const router = useRouter();
    const [jobs, setJobs] = useState<SolverJob[]>(initialJobs);
    const planningUnitIds = useMemo(() => [caseId], [caseId]);
    const storageKey = getSolveJobHistoryKey(monthYear, planningUnitIds);
    const [showFetchWarning, setShowFetchWarning] = useState(false);
    const [showDeleteWarning, setShowDeleteWarning] = useState(false);
    const [showInsertWarning, setShowInsertWarning] = useState(false);
    const [showTimeoutDialog, setShowTimeoutDialog] = useState(false);
    const [pendingAction, setPendingAction] = useState<'solve' | 'multi-solve' | null>(null);
    const [executingAction, setExecutingAction] = useState<WorkflowAction | null>(null);
    const [executingTimeout, setExecutingTimeout] = useState<number>(60);
    const [actionStates, setActionStates] = useState<Record<WorkflowAction, ActionState>>({
        delete: {status: 'idle'},
        fetch: {status: 'idle'},
        solve: {status: 'idle'},
        'multi-solve': {status: 'idle'},
        insert: {status: 'idle'},
        'edit-wishes': {status: 'idle'},
    });

    const saveJobs = useCallback((nextJobs: SolverJob[]) => {
        const lastJobs = writeSolveJobHistory(storageKey, planningUnitIds, nextJobs);
        setJobs(lastJobs);
    }, [planningUnitIds, storageKey]);

    const refreshJob = useCallback(async (job: SolverJob) => {
        if (job.type !== 'solve' || !job.backendJobId) return;
        try {
            const result = await checkSolveJob(caseId, job.params as SolveParams, job.backendJobId);
            if (!result.success) return;
            saveJobs(jobs.map(item => item.id === job.id ? result.data.job : item));
        } catch {
            // keep stored job if the backend cannot be reached
        }
    }, [caseId, jobs, saveJobs]);

    const refreshJobs = useCallback(async () => {
        const checkedJobs = await Promise.all(jobs.map(async job => {
            if (job.type !== 'solve' || !job.backendJobId) return job;
            const result = await checkSolveJob(caseId, job.params as SolveParams, job.backendJobId);
            return result.success ? result.data.job : job;
        }));
        saveJobs(checkedJobs);
    }, [caseId, jobs, saveJobs]);

    const addJob = useCallback((job: SolverJob) => {
        saveJobs([job, ...jobs.filter(item => item.id !== job.id)]);
    }, [jobs, saveJobs]);

    useEffect(() => {
        const timeoutId = window.setTimeout(() => {
            try {
                setJobs(readSolveJobHistory(storageKey));
            } catch {
                setJobs([]);
            }
        }, 0);
        return () => window.clearTimeout(timeoutId);
    }, [storageKey]);

    useEffect(() => {
        if (jobs.length === 0) return;
        const intervalId = setInterval(refreshJobs, 10_000);
        return () => clearInterval(intervalId);
    }, [jobs.length, refreshJobs]);

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
    } = useSolverOperations({onAfterOperation: refreshJobs, onSolveJobStarted: addJob, initialLastInsertedSolution, initialPendingInsertSolution});

    const execOpts = {caseId, monthYear, start: isoStart, end: isoEnd};

    const runAction = async (action: WorkflowAction, timeout?: number) => {
        setActionStates(prev => ({...prev, [action]: {status: 'running'}}));
        setExecutingAction(action);
        setExecutingTimeout(timeout ?? 60);
        let succeeded = false;
        try {
            switch (action) {
                case 'delete': {
                    const r = await executeDelete(execOpts);
                    succeeded = r.succeeded;
                    break;
                }
                case 'fetch': {
                    const r = await executeFetch(execOpts);
                    succeeded = r.succeeded;
                    break;
                }
                case 'solve': {
                    const r = await executeSolve(execOpts, timeout ?? 60);
                    succeeded = r.succeeded;
                    break;
                }
                case 'multi-solve': {
                    const r = await executeSolveMultiple(execOpts, timeout ?? 60);
                    succeeded = r.succeeded;
                    break;
                }
                case 'insert': {
                    const r = await executeInsert(execOpts);
                    succeeded = r.succeeded;
                    break;
                }
            }
            setActionStates(prev => ({
                ...prev,
                [action]: {status: succeeded ? 'success' : 'error'},
            }));
        } catch {
            setActionStates(prev => ({...prev, [action]: {status: 'error'}}));
        }
    };

    const executeAction = (action: WorkflowAction) => {
        if (action === 'edit-wishes') {
            router.push(`/wishes-and-blocked?caseId=${caseId}&monthYear=${monthYear}`);
            return;
        }
        if (action === 'fetch') {
            setShowFetchWarning(true);
            return;
        }
        if (action === 'solve' || action === 'multi-solve') {
            setPendingAction(action);
            setShowTimeoutDialog(true);
            return;
        }
        // guard delete/insert when no plan data available
        if (action === 'delete' && !lastInsertedSolution) {
            setShowDeleteWarning(true);
            return;
        }
        if (action === 'insert' && !pendingInsertSolution) {
            setShowInsertWarning(true);
            return;
        }
        runAction(action);
    };

    const handleTimeoutConfirm = (timeout: number) => {
        if (!pendingAction) return;
        const action = pendingAction;
        setPendingAction(null);
        setShowTimeoutDialog(false);
        runAction(action, timeout);
    };

    const formatDate = (dateStr: string): string => dateStr;

    const getActionLabel = (action: WorkflowAction): string => ({
        delete: 'Dienstplan löschen',
        fetch: 'Daten holen',
        solve: 'Dienstplan berechnen',
        'multi-solve': 'Mehrere Dienstpläne berechnen',
        insert: 'Dienstplan exportieren',
        'edit-wishes': 'Wünsche bearbeiten',
    }[action]);

    const getActionDescription = (action: WorkflowAction): string => ({
        delete: 'Löscht den hochgeladenen Dienstplan aus TimeOffice',
        fetch: 'Lädt aktuelle Mitarbeiter- und Wunschdaten aus TimeOffice',
        solve: 'Berechnet eine optimale Lösung für den Dienstplan',
        'multi-solve': 'Berechnet mehrere alternative Lösungen zur Auswahl',
        insert: 'Exportiert den ausgewählten Dienstplan zurück nach TimeOffice',
        'edit-wishes': 'Bearbeiten Sie Wünsche und Blockierungen der Mitarbeiter',
    }[action]);

    const getActionIcon = (action: WorkflowAction) => {
        const state = actionStates[action];
        if (state.status === 'running') return <Loader2 className="h-6 w-6 animate-spin"/>;
        if (state.status === 'success') return <CheckCircle2 className="h-6 w-6 text-green-600"/>;
        if (state.status === 'error') return <AlertCircle className="h-6 w-6 text-red-600"/>;
        const icons: Record<WorkflowAction, React.ReactElement> = {
            delete: <Trash2 className="h-6 w-6"/>,
            fetch: <Download className="h-6 w-6"/>,
            solve: <Play className="h-6 w-6"/>,
            'multi-solve': <PlayCircle className="h-6 w-6"/>,
            insert: <Upload className="h-6 w-6"/>,
            'edit-wishes': <Edit className="h-6 w-6"/>,
        };
        return icons[action];
    };

    const getActionButtonVariant = (action: WorkflowAction): 'default' | 'outline' | 'secondary' =>
        actionStates[action].status === 'success' ? 'outline' : 'default';

    const isActionDisabled = (action: WorkflowAction): boolean => {
        if (!initialConfig?.healthy) return true;
        return actionStates[action].status === 'running' || isExecuting;
    };

    const actions: WorkflowAction[] = ['delete', 'fetch', 'edit-wishes', 'solve', 'multi-solve', 'insert'];

    return (
        <div className="container mx-auto py-8 px-4 max-w-7xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Dienstplan-Workflow</h1>
                <p className="text-muted-foreground">Wählen Sie die gewünschten Aktionen aus</p>
            </div>

            {initialConfig && !initialConfig.healthy && (
                <Alert variant="destructive" className="mb-6">
                    <AlertCircle className="h-4 w-4"/>
                    <AlertTitle>Solver nicht erreichbar</AlertTitle>
                    <AlertDescription>
                        {initialConfig.message}
                        {initialConfig.details && (
                            <span className="block mt-1 text-xs opacity-75">{initialConfig.details}</span>
                        )}
                    </AlertDescription>
                </Alert>
            )}

            <Card className="mb-6">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FolderOpen className="h-5 w-5"/>
                        Planungseinheit &amp; Zeitraum
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Planungseinheit</p>
                            <Badge variant="secondary" className="text-lg px-3 py-1">
                                Case {caseId}
                            </Badge>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Von</p>
                            <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground"/>
                                <span className="font-medium">{formatDate(startDate)}</span>
                            </div>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Bis</p>
                            <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground"/>
                                <span className="font-medium">{formatDate(endDate)}</span>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Progress bar — shown during any solver operation */}
            {isExecuting && (
                <div className="mb-6">
                    <SolverProgressDisplay
                        progress={progress}
                        phase={phase}
                        isIndeterminate={isIndeterminate}
                        runLabel={runLabel}
                        command={
                            executingAction === 'solve' ? 'solve' :
                            executingAction === 'multi-solve' ? 'solve-multiple' : 'fetch'
                        }
                        timeout={executingTimeout}
                    />
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {actions.map((action) => {
                    const state = actionStates[action];

                    return (
                        <Card
                            key={action}
                            className={
                                `flex flex-col h-full ${
                                    state.status === 'success' ? 'border-green-200 bg-green-50/50' :
                                    state.status === 'error' ? 'border-red-200 bg-red-50/50' :
                                    state.status === 'running' ? 'border-blue-200 bg-blue-50/50' : ''
                                }`
                            }
                        >
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            {getActionIcon(action)}
                                            {getActionLabel(action)}
                                        </CardTitle>
                                        <CardDescription className="mt-1">
                                            {getActionDescription(action)}
                                        </CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="flex flex-col grow justify-between">
                                <div>
                                    {state.message && (
                                        <Alert className="mb-4" variant={state.status === 'error' ? 'destructive' : 'default'}>
                                            <AlertDescription>{state.message}</AlertDescription>
                                        </Alert>
                                    )}

                                    {/* additional info for insert/delete */}
                                    {action === 'insert' && (
                                        <div className={`flex items-center gap-1.5 text-xs mb-2 ${pendingInsertSolution ? 'text-green-600' : 'text-muted-foreground'}`}>
                                            {pendingInsertSolution
                                                ? <><CheckCircle2 className="h-3.5 w-3.5"/>Lösung bereit für Einspielung</>
                                                : <><Info className="h-3.5 w-3.5"/>Keine Lösung im Speicher -  API/CLI versucht den Dienstplan auf der Disk zu finden</>
                                            }
                                        </div>
                                    )}
                                    {action === 'delete' && (
                                        <div className={`flex items-center gap-1.5 text-xs mb-2 ${lastInsertedSolution ? 'text-green-600' : 'text-muted-foreground'}`}>
                                            {lastInsertedSolution
                                                ? <><CheckCircle2 className="h-3.5 w-3.5"/>Letzte eingespielten Lösung vorhanden - wird direkt übergeben</>
                                                : <><Info className="h-3.5 w-3.5"/>Keine eingespielte Lösung im Speicher - API/CLI versucht den Dienstplan auf der Disk zu finden</>
                                            }
                                        </div>
                                    )}
                                </div>

                                <Button
                                    onClick={() => executeAction(action)}
                                    disabled={isActionDisabled(action)}
                                    variant={getActionButtonVariant(action)}
                                    className="w-full mt-4"
                                >
                                    {state.status === 'running' && (
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
                                    )}
                                    {state.status === 'success' ? 'Erneut ausführen' : 'Ausführen'}
                                </Button>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Job History Table */}
            <div className="mt-8">
                <JobHistoryTable jobs={jobs} onRefreshJob={refreshJob}/>
            </div>


            {/* Fetch Warning Dialog */}
            <AlertDialog open={showFetchWarning} onOpenChange={setShowFetchWarning}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-600"/>
                            Wünsche werden überschrieben
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Beim Laden der Daten aus TimeOffice werden die aktuellen Wünsche und Blockierungen
                            überschrieben.
                            <br/><br/>
                            Stellen Sie sicher, dass Sie alle wichtigen Änderungen gespeichert haben.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={() => {
                            setShowFetchWarning(false);
                            runAction('fetch');
                        }}>
                            Fortfahren
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Delete warning when no lastInsertedSolution */}
            <AlertDialog open={showDeleteWarning} onOpenChange={setShowDeleteWarning}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-600"/>
                            Löschen ohne eingespielten Plan
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Es ist kein zuletzt eingespielter Dienstplan vorhanden. Der Löschvorgang
                            versucht die Daten auf der Disk zu finden (CLI-Verhalten).
                            <br/><br/>
                            Möchten Sie trotzdem fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={() => {
                            setShowDeleteWarning(false);
                            runAction('delete');
                        }}>
                            Fortfahren
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Insert warning when no pendingInsertSolution */}
            <AlertDialog open={showInsertWarning} onOpenChange={setShowInsertWarning}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-600"/>
                            Export ohne Plan im Speicher
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Es befindet sich derzeit kein Dienstplan im Speicher. Beim Export werden die
                            Daten von der Festplatte verwendet.
                            <br/><br/>
                            Fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                        <AlertDialogAction onClick={() => {
                            setShowInsertWarning(false);
                            runAction('insert');
                        }}>
                            Fortfahren
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Import solution dialog */}
            {importDialogParams && (
                <ImportSolutionDialog
                    open={showImportDialog}
                    onOpenChange={setShowImportDialog}
                    caseId={importDialogParams.caseId}
                    start={importDialogParams.start}
                    end={importDialogParams.end}
                    solutionType={importDialogParams.solutionType}
                    onImport={(params) => handleImport(caseId, monthYear, {
                        ...params,
                        solution: importDialogParams.solution,
                    })}
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
                    onImport={(params) => handleImport(caseId, monthYear, {
                        ...params,
                        solution: multipleImportDialogParams.solutions[params.solutionIndex ?? 0],
                    })}
                    isImporting={isImporting}
                />
            )}

            {/* Timeout configuration dialog */}
            <TimeoutConfigDialog
                open={showTimeoutDialog}
                onOpenChange={setShowTimeoutDialog}
                onConfirm={handleTimeoutConfirm}
                isExecuting={pendingAction ? actionStates[pendingAction].status === 'running' : false}
                actionTitle={pendingAction ? getActionLabel(pendingAction) : ''}
            />
        </div>
    );
}
