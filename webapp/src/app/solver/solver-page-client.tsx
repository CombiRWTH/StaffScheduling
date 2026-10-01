'use client';

import {useCallback, useEffect, useMemo, useState} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {Button} from '@/components/ui/button';
import {ConfigValidator} from '@/features/solver/components/config-validator';
import {SolverControlPanel} from '@/features/solver/components/solver-control-panel';
import {JobHistoryTable} from '@/features/solver/components/job-history-table';
import {checkSolveJob} from '@/features/solver/solver.actions';
import {
    getSolveJobHistoryKey,
    readSolveJobHistory,
    writeSolveJobHistory,
} from '@/features/solver/solve-job-history-storage';
import type {SolveParams, SolverJob} from '@/entities/models/solver.model';
import type {SolverHealthResult} from '@/application/ports/solver.service';
import type {ScheduleSolutionRaw} from '@/entities/models/schedule.model';

interface SolverPageClientProps {
    caseId: number | null;
    monthYear: string;
    availableCaseIds: number[];
    initialConfigValidation: SolverHealthResult | null;
    initialJobs: SolverJob[];
    initialLastInsertedSolution: ScheduleSolutionRaw | null;
    initialPendingInsertSolution: ScheduleSolutionRaw | null;
    isLocked?: boolean;
}

export function SolverPageClient({
                                     caseId,
                                     monthYear,
                                     availableCaseIds,
                                     initialConfigValidation,
                                     initialJobs,
                                     initialLastInsertedSolution,
                                     initialPendingInsertSolution,
                                     isLocked,
                                 }: SolverPageClientProps) {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();

    const [jobs, setJobs] = useState<SolverJob[]>(initialJobs);

    const visibleCaseIds = useMemo(() => {
        const caseIdsParam =
            searchParams.get('caseIds') ?? searchParams.get('caseId') ?? '';

        return Array.from(
            new Set(
                caseIdsParam
                    .split(',')
                    .map(Number)
                    .filter(id => Number.isInteger(id) && id > 0)
            )
        );
    }, [searchParams]);

    const selectedAvailableCaseIds = useMemo(
        () => visibleCaseIds.filter(id => availableCaseIds.includes(id)),
        [availableCaseIds, visibleCaseIds]
    );

    const selectedPlanningUnitIds = useMemo(
        () => selectedAvailableCaseIds.length > 0 ? selectedAvailableCaseIds : caseId ? [caseId] : [],
        [caseId, selectedAvailableCaseIds]
    );

    const storageKey = selectedPlanningUnitIds.length > 0
        ? getSolveJobHistoryKey(monthYear, selectedPlanningUnitIds)
        : null;

    const toggleCase = (selectedCaseId: number) => {
        const nextCaseIds = visibleCaseIds.includes(selectedCaseId)
            ? visibleCaseIds.filter(id => id !== selectedCaseId)
            : [...visibleCaseIds, selectedCaseId];

        const params = new URLSearchParams(searchParams.toString());

        if (nextCaseIds.length > 0) {
            params.set('caseIds', nextCaseIds.join(','));
            params.set('caseId', String(nextCaseIds[0]));
        } else {
            params.delete('caseIds');
            params.delete('caseId');
        }

        router.push(`${pathname}?${params.toString()}`);
    };

    const saveJobs = useCallback((nextJobs: SolverJob[]) => {
        const lastJobs = storageKey
            ? writeSolveJobHistory(storageKey, selectedPlanningUnitIds, nextJobs)
            : nextJobs.slice(0, 10);

        setJobs(lastJobs);
    }, [selectedPlanningUnitIds, storageKey]);

    const refreshJob = useCallback(async (job: SolverJob) => {
        if (!caseId || job.type !== 'solve' || !job.backendJobId) return;
        try {
            const result = await checkSolveJob(caseId, job.params as SolveParams, job.backendJobId);
            if (!result.success) return;
            saveJobs(jobs.map(item => item.id === job.id ? result.data.job : item));
        } catch {
            // keep stored job if the backend cannot be reached
        }
    }, [caseId, jobs, saveJobs]);

    const refreshJobs = useCallback(async () => {
        if (!caseId) return;
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
        if (!storageKey) return;
        const timeoutId = window.setTimeout(() => {
            const storedJobs = localStorage.getItem(storageKey);
            try {
                setJobs(storedJobs ? readSolveJobHistory(storageKey) : []);
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

    return (
        <div className="space-y-6 py-6">
            <div>
                <h1 className="text-3xl font-bold">Solver</h1>
                <p className="text-muted-foreground mt-2">
                    Steuern Sie den Python-Solver zur automatischen Dienstplanerstellung
                </p>
            </div>

            <div className="flex flex-wrap gap-2">
                {availableCaseIds.map(availableCaseId => {
                    const active = selectedAvailableCaseIds.includes(availableCaseId);

                    return (
                        <Button
                            key={availableCaseId}
                            type="button"
                            size="sm"
                            variant={active ? 'default' : 'outline'}
                            onClick={() => toggleCase(availableCaseId)}
                            disabled={isLocked}
                        >
                            Case {availableCaseId}
                        </Button>
                    );
                })}
            </div>

            <ConfigValidator initialData={initialConfigValidation} />

            {!caseId ? (
                <div className="flex items-center justify-center h-64 text-muted-foreground">
                    Bitte wähle mindestens einen Case aus
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <SolverControlPanel
                        caseId={caseId}
                        selectedCaseIds={selectedAvailableCaseIds}
                        monthYear={monthYear}
                        onAfterOperation={refreshJobs}
                        onSolveJobStarted={addJob}
                        initialLastInsertedSolution={initialLastInsertedSolution}
                        initialPendingInsertSolution={initialPendingInsertSolution}
                    />

                    <div className="space-y-6">
                        <JobHistoryTable jobs={jobs} onRefreshJob={refreshJob} />
                    </div>
                </div>
            )}
        </div>
    );
}
