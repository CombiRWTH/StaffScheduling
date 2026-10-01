'use client';

import React, {useState} from 'react';
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
import {Loader2} from 'lucide-react';

interface ImportSolutionDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    caseId: number;
    start: string;
    end: string;
    solutionType: 'wdefault' | string; // wdefault, w0, w1, w2, etc.
    onImport: (params: {
        caseId: number;
        start: string;
        end: string;
        solutionType: string;
    }) => Promise<void>;
    isImporting: boolean;
}

/**
 * Dialog that prompts the user to import a processed solution file
 * after solve or solve-multiple execution.
 */
export function ImportSolutionDialog({
                                         open,
                                         onOpenChange,
                                         caseId,
                                         start,
                                         end,
                                         solutionType,
                                         onImport,
                                         isImporting,
                                     }: ImportSolutionDialogProps) {
    const [error, setError] = useState<string | null>(null);

    // Reset state when dialog is closed
    React.useEffect(() => {
        if (!open) {
            setError(null);
        }
    }, [open]);

    const handleImport = async () => {
        setError(null);
        try {
            await onImport({caseId, start, end, solutionType});
            onOpenChange(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Fehler beim Importieren');
        }
    };

    const handleCancel = () => {
        setError(null);
        onOpenChange(false);
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('de-DE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        });
    };

    // Expected filename format: solution_{caseId}_{start}-{end}_{solutionType}_processed.json
    const expectedFilename = `solution_${caseId}_${start}-${end}_${solutionType}_processed.json`;

    return (
        <AlertDialog open={open} onOpenChange={onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Lösung automatisch importieren?</AlertDialogTitle>
                    <AlertDialogDescription>
                        Der Solver hat erfolgreich eine Lösung erstellt. Möchten Sie diese
                        automatisch als Schedule importieren?
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <div className="space-y-3">
                    <div className="rounded-md bg-muted p-3 text-sm">
                        <div className="font-medium mb-1">Details:</div>
                        <div className="space-y-1 text-muted-foreground">
                            <div>Fall: {caseId}</div>
                            <div>Zeitraum: {formatDate(start)} - {formatDate(end)}</div>
                            <div>Typ: {solutionType}</div>
                            <div className="text-xs mt-2 break-all">
                                Datei: {expectedFilename}
                            </div>
                        </div>
                    </div>
                    {error && (
                        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                            {error}
                        </div>
                    )}
                </div>
                <AlertDialogFooter>
                    <AlertDialogCancel onClick={handleCancel} disabled={isImporting}>
                        Abbrechen
                    </AlertDialogCancel>
                    <AlertDialogAction onClick={handleImport} disabled={isImporting}>
                        {isImporting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
                                Importiere...
                            </>
                        ) : (
                            'Importieren'
                        )}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
