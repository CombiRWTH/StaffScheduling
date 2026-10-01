'use client';

import {usePathname, useRouter, useSearchParams} from 'next/navigation';
import {useEffect, useState} from 'react';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from '@/components/ui/select';
import {Button} from '@/components/ui/button';
import {FetchCaseDialog} from '@/features/cases/components/fetch-case-dialog';
import {Plus} from 'lucide-react';
import {parseMonthYear} from '@/lib/utils/case-utils';
import {CaseUnit} from '@/entities/models/case.model';
import {listCasesAction} from '@/features/cases/cases.actions';


interface CaseSelectorProps {
    disabled?: boolean;
    lockedCaseId?: number | null;
    lockedMonthYear?: string | null;
}

export function CaseSelector({disabled, lockedCaseId, lockedMonthYear}: CaseSelectorProps) {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();

    const [dialogOpen, setDialogOpen] = useState(false);

    const urlCaseIdStr = searchParams.get('caseId');
    const urlMonthYear = searchParams.get('monthYear');

    // Use the locked workflow values when navigation is fixed; otherwise read from the URL.
    const effectiveCaseId = disabled && lockedCaseId
        ? lockedCaseId
        : (urlCaseIdStr ? parseInt(urlCaseIdStr, 10) : null);

    const effectiveMonthYear = disabled && lockedMonthYear
        ? lockedMonthYear
        : (urlMonthYear ?? '');


    const [availableCases, setAvailableCases] = useState<CaseUnit[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const refreshCases = async () => {
        setIsLoading(true);
        try {
            const data = await listCasesAction();
            setAvailableCases(data.units ?? []);
        } catch {
            setAvailableCases([]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        refreshCases();
    }, []);

    // Build a flat list of all case options for the selector
    const allCaseOptions = availableCases.flatMap(unit =>
        unit.months.map(monthYear => ({
            unitId: unit.unitId,
            monthYear,
            ...parseMonthYear(monthYear)
        }))
    );

    const getMonthName = (month: number) =>
        new Date(0, month - 1).toLocaleString('de-DE', {month: 'long'});

    const handleCaseChange = (value: string) => {
        const [unitIdStr, my] = value.split('|');
        const params = new URLSearchParams(searchParams.toString());
        params.set('caseId', unitIdStr);
        params.set('monthYear', my);
        router.push(`${pathname}?${params.toString()}`);
    };


    const currentValue = effectiveCaseId && effectiveMonthYear
        ? `${effectiveCaseId}|${effectiveMonthYear}`
        : '';


    return (
        <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Case:</span>
            <Select
                value={currentValue}
                onValueChange={handleCaseChange}
                disabled={disabled || isLoading}
            >
                <SelectTrigger className="w-[280px]">
                    <SelectValue placeholder={
                        disabled && lockedCaseId && lockedMonthYear
                            ? `Case ${lockedCaseId} - ${lockedMonthYear.replace('_', ' ')}`
                            : "Wähle Case"
                    }/>
                </SelectTrigger>
                <SelectContent>
                    {allCaseOptions.map((option) => (
                        <SelectItem
                            key={`${option.unitId}|${option.monthYear}`}
                            value={`${option.unitId}|${option.monthYear}`}
                        >
                            Case {option.unitId} - {getMonthName(option.month)} {option.year}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>

            {/* Add button next to the dropdown */}
            <Button
                size="sm"
                className="ml-2"
                disabled={disabled || isLoading}
                onClick={() => setDialogOpen(true)}
            >
                <Plus className="h-4 w-4" />
            </Button>

            <FetchCaseDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                initialCaseId={effectiveCaseId ?? undefined}
                onFetched={(cid, my) => {
                    refreshCases();
                    const params = new URLSearchParams(searchParams.toString());
                    params.set('caseId', String(cid));
                    params.set('monthYear', my);
                    router.push(`${pathname}?${params.toString()}`);
                }}
            />
        </div>
    );
}
