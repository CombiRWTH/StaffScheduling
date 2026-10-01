'use client';

import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow,} from '@/components/ui/table';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {CheckCircle2, ChevronDown, ChevronUp, Loader2, XCircle} from 'lucide-react';
import {SolverJob} from '@/entities/models/solver.model';
import {useState} from 'react';
import {format} from 'date-fns';
import {de} from 'date-fns/locale';

function JobRow({job, onRefreshJob}: { job: SolverJob; onRefreshJob?: (job: SolverJob) => Promise<void> | void }) {
    const [expanded, setExpanded] = useState(false);
    const isInfeasible =
        (job.type === 'solve' || job.type === 'solve-multiple') &&
        (job.status === 'completed' || job.status === 'succeeded') &&
        typeof job.result === 'object' && job.result !== null &&
        'status' in job.result && job.result.status === 'infeasible';

    const getCommandLabel = (type: string) => {
        const labels: Record<string, string> = {
            fetch: 'Daten abrufen',
            solve: 'Lösen',
            'solve-multiple': 'Mehrfach lösen',
            insert: 'Einfügen',
            delete: 'Löschen',
        };
        return labels[type] || type;
    };

    const handleClick = async () => {
        await onRefreshJob?.(job);
        setExpanded(!expanded);
    };

    const renderStatus = () => {
        if (job.status === 'accepted' || job.status === 'running') {
            return (
                <Badge variant="secondary">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin"/>
                    {job.status === 'accepted' ? 'Angenommen' : 'Läuft'}
                </Badge>
            );
        }

        if ((job.status === 'completed' || job.status === 'succeeded') && !isInfeasible) {
            return job.type === 'solve-multiple' && job.metadata?.solutionsGenerated !== undefined && job.metadata?.expectedSolutions !== undefined ? (
                job.metadata.solutionsGenerated < job.metadata.expectedSolutions ? (
                    <Badge variant="default"
                           className="bg-yellow-600 dark:bg-yellow-600 hover:bg-yellow-700 dark:hover:bg-yellow-700">
                        <CheckCircle2 className="h-3 w-3 mr-1"/>
                        Teilweise ({job.metadata.solutionsGenerated}/{job.metadata.expectedSolutions})
                    </Badge>
                ) : (
                    <Badge variant="default"
                           className="bg-green-600 dark:bg-green-600 hover:bg-green-700 dark:hover:bg-green-700">
                        <CheckCircle2 className="h-3 w-3 mr-1"/>
                        Erfolgreich
                    </Badge>
                )
            ) : (
                <Badge variant="default"
                       className="bg-green-600 dark:bg-green-600 hover:bg-green-700 dark:hover:bg-green-700">
                    <CheckCircle2 className="h-3 w-3 mr-1"/>
                    Erfolgreich
                </Badge>
            );
        }

        return (
            <Badge variant="destructive">
                <XCircle className="h-3 w-3 mr-1"/>
                Fehlgeschlagen
            </Badge>
        );
    };

    return (
        <>
            <TableRow className="cursor-pointer hover:bg-muted/50" onClick={handleClick}>
                <TableCell className="font-medium">
                    {getCommandLabel(job.type)}
                </TableCell>
                <TableCell>
                    {renderStatus()}
                    {isInfeasible && (
                        <p className="mt-1 text-xs text-muted-foreground">Keine zulässige Lösung</p>
                    )}
                </TableCell>
                <TableCell>
                    {format(new Date(job.createdAt), 'dd.MM.yyyy HH:mm', {locale: de})}
                </TableCell>
                <TableCell>{job.duration != null ? `${(job.duration / 1000).toFixed(1)}s` : '-'}</TableCell>
                <TableCell>
                    <Button variant="ghost" size="sm">
                        {expanded ? <ChevronUp className="h-4 w-4"/> : <ChevronDown className="h-4 w-4"/>}
                    </Button>
                </TableCell>
            </TableRow>
            {expanded && (
                <TableRow>
                    <TableCell colSpan={5} className="bg-muted/30">
                        <div className="p-4 space-y-3">
                            {isInfeasible && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Solver-Ergebnis:</p>
                                    <p className="text-sm text-muted-foreground">
                                        Der Solver wurde erfolgreich ausgeführt, hat aber keine zulässige Lösung gefunden (infeasible).
                                    </p>
                                </div>
                            )}
                            <div>
                                <p className="text-sm font-medium mb-1">Parameter:</p>
                                <pre
                                    className="text-xs bg-background p-2 rounded overflow-auto wrap-break-word whitespace-pre-wrap">
                  {JSON.stringify(job.params, null, 2)}
                </pre>
                            </div>

                            {job.consoleOutput && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Konsolen-Output:</p>
                                    <pre
                                        className="text-xs bg-background p-2 rounded overflow-auto max-h-40 e wrap-break-word whitespace-pre-wrap">
                    {job.consoleOutput}
                  </pre>
                                </div>
                            )}
                            {job.error && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Fehler:</p>
                                    <pre
                                        className="text-xs bg-background p-2 rounded overflow-auto max-h-40 wrap-break-word whitespace-pre-wrap">
                    {job.error}
                  </pre>
                                </div>
                            )}
                        </div>
                    </TableCell>
                </TableRow>
            )}
        </>
    );
}

interface JobHistoryTableProps {
    jobs: SolverJob[];
    onRefreshJob?: (job: SolverJob) => Promise<void> | void;
}

export function JobHistoryTable({jobs, onRefreshJob}: JobHistoryTableProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Job-Verlauf</CardTitle>
                <CardDescription>
                    Letzte {jobs.length} ausgeführte Befehle (max. 10)
                </CardDescription>
            </CardHeader>
            <CardContent>
                {jobs.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                        Noch keine Jobs ausgeführt
                    </p>
                ) : (
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Befehl</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Zeitpunkt</TableHead>
                                    <TableHead>Dauer</TableHead>
                                    <TableHead></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {jobs.map((job) => (
                                    <JobRow key={job.id} job={job} onRefreshJob={onRefreshJob}/>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
