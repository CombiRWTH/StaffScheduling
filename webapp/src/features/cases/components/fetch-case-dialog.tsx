'use client';

import {useState, useEffect} from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {Label} from '@/components/ui/label';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/select';
import {Input} from '@/components/ui/input';
import {useSolverOperations} from '@/features/solver/hooks/use-solver-operations';

interface FetchCaseDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    initialCaseId?: number | null;
    /**
     * called after a successful fetch so the parent can react
     * (e.g. update the URL / refresh selector list)
     */
    onFetched: (caseId: number, monthYear: string) => void;
}

export function FetchCaseDialog({
    open,
    onOpenChange,
    initialCaseId,
    onFetched,
}: FetchCaseDialogProps) {
    const [caseId, setCaseId] = useState(initialCaseId ?? 0);
    const [month, setMonth] = useState<number | null>(null);
    const [year, setYear] = useState<number | null>(null);

    // reset fields whenever dialog opens; use timeout to avoid React warning about
    // "setState synchronously within an effect" which would show during dev.
    useEffect(() => {
        if (!open) return;
        const id = setTimeout(() => {
            setCaseId(initialCaseId ?? 0);
            setMonth(null);
            setYear(null);
        }, 0);
        return () => clearTimeout(id);
    }, [open, initialCaseId]);

    // same refresh logic as in CaseSelector
    const {executeFetch, isExecuting: isFetching} = useSolverOperations({
        onAfterOperation: async () => {
            // parent will refresh via onFetched callback
        },
    });

    const handleSubmit = async () => {
        if (!caseId || month === null || year === null) return;
        const monthStr = String(month).padStart(2, '0');
        const newMonthYear = `${monthStr}_${year}`;

        const firstDay = new Date(year, month - 1, 1);
        const lastDay = new Date(year, month, 0);
        const start = `${firstDay.getFullYear()}-${String(firstDay.getMonth() + 1).padStart(2, '0')}-${String(firstDay.getDate()).padStart(2, '0')}`;
        const end = `${lastDay.getFullYear()}-${String(lastDay.getMonth() + 1).padStart(2, '0')}-${String(lastDay.getDate()).padStart(2, '0')}`;

        const result = await executeFetch({caseId, monthYear: newMonthYear, start, end});
        if (result.succeeded) {
            onFetched(caseId, newMonthYear);
            onOpenChange(false);
        }
    };

    const monthOptions = Array.from({length: 12}, (_, i) => ({
        value: i + 1,
        label: new Date(0, i).toLocaleString('de-DE', {month: 'long'}),
    }));

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-sm">
                <DialogHeader>
                    <DialogTitle>Daten abrufen</DialogTitle>
                    <DialogDescription>Wähle Case, Monat und Jahr</DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    <div className="space-y-1">
                        <Label htmlFor="dlg-caseId">Case ID</Label>
                        <Input
                            id="dlg-caseId"
                            type="number"
                            min={1}
                            value={caseId || ''}
                            onChange={(e) => setCaseId(parseInt(e.target.value, 10) || 0)}
                            disabled={isFetching}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <Label htmlFor="dlg-month">Monat</Label>
                            <Select
                                value={month?.toString() || ''}
                                onValueChange={(v) => setMonth(parseInt(v, 10))}
                                disabled={isFetching}
                            >
                                <SelectTrigger id="dlg-month">
                                    <SelectValue placeholder="Monat" />
                                </SelectTrigger>
                                <SelectContent>
                                    {monthOptions.map((m) => (
                                        <SelectItem key={m.value} value={m.value.toString()}>
                                            {m.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1">
                            <Label htmlFor="dlg-year">Jahr</Label>
                            <Select
                                value={year?.toString() || ''}
                                onValueChange={(v) => setYear(parseInt(v, 10))}
                                disabled={isFetching}
                            >
                                <SelectTrigger id="dlg-year">
                                    <SelectValue placeholder="Jahr" />
                                </SelectTrigger>
                                <SelectContent>
                                    {Array.from({length: 15}, (_, i) => new Date().getFullYear() - 5 + i).map((y) => (
                                        <SelectItem key={y} value={y.toString()}>
                                            {y}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isFetching}>
                        Abbrechen
                    </Button>
                    <Button onClick={handleSubmit} disabled={isFetching || !caseId || month === null || year === null}>
                        {isFetching ? '...' : 'Fetch'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
