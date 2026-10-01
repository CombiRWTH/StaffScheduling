'use client';

import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {cn} from '@/lib/utils';
import {ScheduleEmployee, ScheduleSolution, Shift} from '@/entities/models/schedule.model';
import {getEmployeeStats, getShiftsForCell, isWeekend} from '@/lib/services/schedule-parser';
import {Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,} from '@/components/ui/tooltip';
import {Input} from '@/components/ui/input';
import {Search} from 'lucide-react';

/**
 * Neue Typen für die Zusammenfassung:
 * - pro Tag: Gesamtanzahl, pro Schichttyp mit Aufschlüsselung nach Mitarbeitertyp
 */
interface ShiftTypeSummary {
    total: number;
    byEmployeeType: Record<string, number>;
}

interface DayShiftSummary {
    total: number;
    shifts: Record<string, ShiftTypeSummary>; // key: shift.abbreviation || shift.id
}

type ShiftSummary = Record<string, DayShiftSummary>; // key: dateStr 'YYYY-MM-DD'

interface SingleScheduleTableProps {
    employees: ScheduleEmployee[];
    days: Date[];
    shifts: Shift[];
    variables: Record<string, number>;
    fulfilledDayOffCells: Set<string>;
    fulfilledShiftWishCells: Set<string>;
    allDayOffWishCells: Set<string>;
    allShiftWishColors: Record<string, string[]>;
    isFullscreen?: boolean;
    reducedView?: boolean;
    compareMode?: false;
    shiftSummary?: ShiftSummary;
}

interface CompareScheduleTableProps {
    schedules: (ScheduleSolution & { scheduleId: string; description?: string })[];
    reducedView?: boolean;
    compareMode: true;
    isFullscreen?: boolean;
}

type ScheduleTableProps = SingleScheduleTableProps | CompareScheduleTableProps;

const computeShiftSummary = (
    employees: ScheduleEmployee[],
    days: Date[],
    shifts: Shift[],
    variables: Record<string, number>
): ShiftSummary => {
    const summary: ShiftSummary = {};

    days.forEach((day) => {
        const dateStr = day.toISOString().split('T')[0];
        summary[dateStr] = {
            total: 0,
            shifts: {},
        };

        employees.forEach((emp) => {
            const shiftsForCell = getShiftsForCell(emp.id, day, shifts, variables);
            const empType = emp.level || 'unknown';

            if (shiftsForCell.length > 0) {
                summary[dateStr].total += shiftsForCell.length;

                shiftsForCell.forEach((s) => {
                    // We only summarize the main shift types and not the special shifts like S2_, F2_, N5 etc.
                    if (s.name === "Nacht" || s.name === "Früh" || s.name === "Spät" || s.name === "Zwischen") {
                        const key = s.abbreviation || String(s.id);
                        console.log(s.color);
                        if (!summary[dateStr].shifts[key]) {
                            summary[dateStr].shifts[key] = {total: 0, byEmployeeType: {}};
                        }
                        summary[dateStr].shifts[key].total += 1;
                        summary[dateStr].shifts[key].byEmployeeType[empType] =
                            (summary[dateStr].shifts[key].byEmployeeType[empType] || 0) + 1;
                    }
                });
            }
        });
    });
    return summary;
};

/**
 * Displays the complete schedule in a table format.
 */
export function ScheduleTable(props: ScheduleTableProps) {
    const [openTooltipCell, setOpenTooltipCell] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);
    const [portalContainer, setPortalContainer] = useState<HTMLElement | undefined>(undefined);

    const isFullscreen = props.isFullscreen ?? false;
    const compareMode = props.compareMode ?? false;
    const reducedView = props.reducedView ?? null;

    useEffect(() => {
        if (isFullscreen && containerRef.current) {
            setPortalContainer(containerRef.current);
        } else {
            setPortalContainer(undefined);
        }
    }, [isFullscreen]);

    const generateSummaryString = (
        pair: [string, ShiftTypeSummary]
    ): string => {
        const [abbr, info] = pair;

        const levelToInitial = (level: string): string => {
            const l = (level || '').toLowerCase();
            if (l.includes('fach')) return 'F';
            if (l.includes('hilf')) return 'H';
            if (l.includes('azub') || l.includes('ausb')) return 'A';
            return (level && level[0]) ? level[0].toUpperCase() : '?';
        };

        const countsByInitial: Record<string, number> = {};
        Object.entries(info.byEmployeeType || {}).forEach(([level, count]) => {
            const init = levelToInitial(level);
            countsByInitial[init] = (countsByInitial[init] || 0) + (count ?? 0);
        });

        const order = ['F', 'H', 'A'];
        const allZero = order.every(k => !(countsByInitial[k] > 0));
        if (allZero) return '—';

        return order.map(k => `${k}${countsByInitial[k] || 0}`).join('|');
    };

    const handleMouseLeave = useCallback(() => {
        setOpenTooltipCell(null);
    }, []);

    const handleCellClick = useCallback((cellKey: string) => {
        setOpenTooltipCell(cellKey);
    }, []);

    // Check if employee is unavailable for a day/shift
    const unavailable = (employee: ScheduleEmployee, day: number, shift?: Shift) => {
        if (!shift) {
            return (
                employee.vacation_days.includes(day) ||
                employee.forbidden_days.includes(day)
            );
        }
        return (
            employee.vacation_shifts.some(
                ([d, s]: [number, string]) => d === day && s === shift.abbreviation
            ) ||
            employee.forbidden_shifts.some(
                ([d, s]: [number, string]) => d === day && s === shift.abbreviation
            )
        );
    };

    // Extract common data based on mode and compute shiftSummary
    const {
        employees,
        days,
        shifts,
        variables,
        fulfilledDayOffCells,
        fulfilledShiftWishCells,
        allDayOffWishCells,
        allShiftWishColors,
        shiftSummary
    } = useMemo(() => {
        let base: {
            employees: ScheduleEmployee[];
            days: Date[];
            shifts: Shift[];
            variables: Record<string, number>;
            fulfilledDayOffCells: Set<string>;
            fulfilledShiftWishCells: Set<string>;
            allDayOffWishCells: Set<string>;
            allShiftWishColors: Record<string, string[]>;
        };

        if (compareMode && 'schedules' in props) {
            const firstSchedule = props.schedules[0];
            base = {
                employees: firstSchedule.employees,
                days: firstSchedule.days,
                shifts: firstSchedule.shifts,
                variables: firstSchedule.variables,
                fulfilledDayOffCells: firstSchedule.fulfilledDayOffCells,
                fulfilledShiftWishCells: firstSchedule.fulfilledShiftWishCells,
                allDayOffWishCells: firstSchedule.allDayOffWishCells,
                allShiftWishColors: firstSchedule.allShiftWishColors,
            };
        } else if (!compareMode && 'employees' in props) {
            base = {
                employees: props.employees,
                days: props.days,
                shifts: props.shifts,
                variables: props.variables,
                fulfilledDayOffCells: props.fulfilledDayOffCells,
                fulfilledShiftWishCells: props.fulfilledShiftWishCells,
                allDayOffWishCells: props.allDayOffWishCells,
                allShiftWishColors: props.allShiftWishColors,
            };
        } else {
            // Fallback (should never happen)
            base = {
                employees: [],
                days: [],
                shifts: [],
                variables: {},
                fulfilledDayOffCells: new Set<string>(),
                fulfilledShiftWishCells: new Set<string>(),
                allDayOffWishCells: new Set<string>(),
                allShiftWishColors: {},
            };
        }

        const summary = computeShiftSummary(base.employees, base.days, base.shifts, base.variables);

        return {
            ...base,
            shiftSummary: summary,
        };
    }, [compareMode, props]);

    // Compute shift summaries for each schedule when in compare mode
    const scheduleSummaries = useMemo(() => {
        if (!compareMode || !('schedules' in props)) return {} as Record<string, ReturnType<typeof computeShiftSummary>>;
        const schedules = (props as CompareScheduleTableProps).schedules;
        const map: Record<string, ReturnType<typeof computeShiftSummary>> = {};
        schedules.forEach((s) => {
            map[s.scheduleId] = computeShiftSummary(s.employees, s.days, s.shifts, s.variables);
        });
        return map;
    }, [compareMode, props]);

    const filteredEmployees = useMemo(() => {
        if (!searchTerm) return employees;

        const lowerSearch = searchTerm.toLowerCase();
        return employees.filter((employee: ScheduleEmployee) =>
            employee.name.toLowerCase().includes(lowerSearch) ||
            employee.level.toLowerCase().includes(lowerSearch) ||
            employee.id.toString().includes(lowerSearch)
        );
    }, [employees, searchTerm]);

    // Group employees by ID for compare mode
    const groupedEmployees = useMemo(() => {
        if (!compareMode || !('schedules' in props)) return [];

        const schedules = props.schedules;
        const employeeMap = new Map<number, ScheduleEmployee[]>();

        // Group all employees by their ID
        schedules.forEach((schedule: ScheduleSolution & { scheduleId: string; description?: string }) => {
            schedule.employees.forEach((employee: ScheduleEmployee) => {
                if (!employeeMap.has(employee.id)) {
                    employeeMap.set(employee.id, []);
                }
                employeeMap.get(employee.id)!.push(employee);
            });
        });

        // Convert to array of groups, filtering by search
        const groups: {
            employee: ScheduleEmployee;
            scheduleId: string;
            description?: string;
            scheduleData: ScheduleSolution & { scheduleId: string; description?: string }
        }[][] = [];

        employeeMap.forEach((employees, employeeId) => {
            const firstEmployee = employees[0];
            if (!searchTerm ||
                firstEmployee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                firstEmployee.level.toLowerCase().includes(searchTerm.toLowerCase()) ||
                firstEmployee.id.toString().includes(searchTerm)) {

                const group = schedules.map((schedule: ScheduleSolution & {
                    scheduleId: string;
                    description?: string
                }, _idx: number) => {
                    const employee = schedule.employees.find((e: ScheduleEmployee) => e.id === employeeId);
                    return {
                        employee: employee!,
                        scheduleId: schedule.scheduleId,
                        description: schedule.description,
                        scheduleData: schedule,
                    };
                }).filter((item: {
                    employee: ScheduleEmployee;
                    scheduleId: string;
                    description?: string;
                    scheduleData: ScheduleSolution & { scheduleId: string; description?: string }
                }) => item.employee);

                groups.push(group);
            }
        });

        return groups;
    }, [compareMode, props, searchTerm]);

    if (compareMode && 'schedules' in props && (!props.schedules || props.schedules.length === 0)) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                Keine Dienstpläne zum Vergleichen ausgewählt.
            </div>
        );
    }

    return (
        <div className={cn(isFullscreen && "h-full flex flex-col")} ref={containerRef}>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"/>
                <Input
                    placeholder="Suche nach Name, Level oder ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                />
            </div>

            {compareMode ? (
                groupedEmployees.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        Keine Mitarbeiter gefunden.
                    </div>
                ) : reducedView ? (
                        <TooltipProvider delayDuration={300} skipDelayDuration={100}>
                            <div className={cn(
                                "relative overflow-auto",
                                isFullscreen ? "flex-1" : "max-h-[800px]"
                            )}>
                                <table className="w-full border-collapse text-sm">
                                    <thead className="sticky top-0 z-20 bg-card">
                                    <tr>
                                        <th className="sticky left-0 z-30 border-b border-r border-border bg-card p-1 text-left font-semibold text-foreground">
                                            Employee / <br/> Dienstplan
                                        </th>
                                        {days.map((day: Date, idx: number) => (
                                            <th
                                                key={idx}
                                                className={cn(
                                                    'border-b border-border text-center font-medium text-foreground',
                                                    isWeekend(day) && 'bg-muted/30'
                                                )}
                                            >
                                                <div className="font-semibold">
                                                    {day.toLocaleDateString('de-DE', {month: 'numeric', day: 'numeric'})}
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    {day.toLocaleDateString('de-DE', {weekday: 'short'})}
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                    </thead>
                                    <tbody>
                                    {groupedEmployees.map((group, groupIdx) => (
                                        <React.Fragment key={`group-${group[0]?.employee.id || groupIdx}`}>
                                            {group.map((item, itemIdx) => {
                                                const {employee, scheduleId, description, scheduleData} = item;
                                                const stats = getEmployeeStats(employee, scheduleData.days, scheduleData.shifts, scheduleData.variables);
                                                const isFirstInGroup = itemIdx === 0;
                                                const isLastInGroup = itemIdx === group.length - 1;

                                                return (
                                                    <tr
                                                        key={`${employee.id}-${scheduleId}`}
                                                        className={cn(
                                                            "transition-colors",
                                                            !isLastInGroup && "border-b-0"
                                                        )}
                                                    >
                                                        <td
                                                            className={cn(
                                                                'sticky left-0 z-20 border-r border-border p-1',
                                                                stats.hasOvertime
                                                                    ? 'bg-red-50 dark:bg-red-950/40'
                                                                    : 'bg-card',
                                                                isLastInGroup ? 'border-b' : 'border-b-0'
                                                            )}
                                                        >
                                                            {isFirstInGroup && (
                                                                <>
                                                                    <div
                                                                        className="font-medium text-foreground">{employee.name} (<span
                                                                        className="text-xs text-foreground">{employee.level[0]}</span>)
                                                                    </div>
                                                                </>
                                                            )}
                                                            <div
                                                                className={cn("text-xs font-semibold", isFirstInGroup, "text-blue-600 dark:text-blue-400")}>
                                                                {description || "Ohne Beschreibung"}
                                                            </div>
                                                            <div className="text-xs">
                                                                <div
                                                                    className={cn(
                                                                        'font-medium',
                                                                        stats.hasOvertime ? 'text-destructive' : 'text-muted-foreground'
                                                                    )}
                                                                >
                                                                    {stats.actualHours.toFixed(1)}h
                                                                    / {stats.targetHours.toFixed(1)}h
                                                                </div>
                                                            </div>
                                                        </td>
                                                        {scheduleData.days.map((day: Date, dayIdx: number) => {
                                                            const shiftsForCell = getShiftsForCell(employee.id, day, scheduleData.shifts, scheduleData.variables);
                                                            const dateStr = day.toISOString().split('T')[0];
                                                            const cellKey = `${employee.id}-${scheduleId}-${dateStr}`;

                                                            const isDayOffFulfilled = scheduleData.fulfilledDayOffCells.has(`${employee.id}-${dateStr}`);
                                                            const isShiftWishFulfilled = scheduleData.fulfilledShiftWishCells.has(`${employee.id}-${dateStr}`);
                                                            const hasDayOffWish = scheduleData.allDayOffWishCells.has(`${employee.id}-${dateStr}`);

                                                            const isUnavailable = unavailable(employee, dayIdx + 1);

                                                            return (
                                                                <td
                                                                    key={dayIdx}
                                                                    className={cn(
                                                                        'px-2 text-center relative z-0 cursor-pointer hover:bg-foreground/5',
                                                                        isWeekend(day) && 'bg-muted/30 hover:bg-muted/90',
                                                                        isDayOffFulfilled && 'bg-amber-400/10 hover:bg-amber-400/25',
                                                                        isShiftWishFulfilled && 'bg-emerald-400/10 hover:bg-emerald-400/25',
                                                                        isUnavailable && 'bg-rose-400/10 hover:bg-rose-400/25',
                                                                        !shiftsForCell.length && !isDayOffFulfilled && hasDayOffWish && 'bg-rose-400/5 hover:bg-rose-400/20',
                                                                        isLastInGroup ? 'border-b border-border' : 'border-b-0'
                                                                    )}
                                                                    onMouseLeave={() => handleMouseLeave()}
                                                                    onClick={() => handleCellClick(cellKey)}
                                                                >
                                                                    {shiftsForCell.length > 0 ? (
                                                                        <div className="flex flex-col w-full gap-1">
                                                                            {shiftsForCell.map((shift) => (
                                                                                <div
                                                                                    key={shift.id}
                                                                                    className="rounded-md py-1.5 font-medium text-white"
                                                                                    style={{backgroundColor: shift.color}}
                                                                                >
                                                                                    {shift.abbreviation}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <div className="py-1.5"/>
                                                                    )}

                                                                    {openTooltipCell === cellKey && (
                                                                        <Tooltip open={true}>
                                                                            <TooltipTrigger asChild>
                                                                                <div className="absolute inset-0 top-8"/>
                                                                            </TooltipTrigger>
                                                                            <TooltipContent container={portalContainer}>
                                                                                <div className="text-sm space-y-1">
                                                                                    {shiftsForCell.length > 0 && (
                                                                                        <div className="space-y-1">
                                                                                            {shiftsForCell.map((shift) => (
                                                                                                <div key={shift.id}>
                                                                                                    <p className="font-semibold">{shift.name}</p>
                                                                                                    <p className="text-xs text-muted-foreground">
                                                                                                        Dauer: {Math.floor(shift.duration / 60)}h {shift.duration % 60}min
                                                                                                    </p>
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            </TooltipContent>
                                                                        </Tooltip>
                                                                    )}
                                                                </td>
                                                            );
                                                        })}
                                                    </tr>
                                                );
                                            })}
                                        </React.Fragment>
                                    ))}
                                    </tbody>
                                    <tfoot className="sticky bottom-0 bg-card z-30">
                                    {/* Per-Plan summary rows: render one summary row per schedule (stacked) */}
                                    {(props as CompareScheduleTableProps).schedules.map((schedule) => {
                                        const summary = scheduleSummaries[schedule.scheduleId] || {};
                                        return (
                                            <tr key={`summary-${schedule.scheduleId}`} className="border-t">
                                                <td className="sticky bottom-0 left-0 z-30 border-b border-r border-border bg-card text-left font-semibold text-foreground">
                                                    <div className="flex items-center justify-between">
                                                        <div
                                                            className="whitespace-nowrap">{schedule.description || `Plan ${schedule.scheduleId}`}</div>
                                                        <div
                                                            className="text-xs text-muted-foreground flex pr-2 flex-col items-end">
                                                            <div>F</div>
                                                            <div>Z</div>
                                                            <div>S</div>
                                                            <div>N</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                {schedule.days.map((day: Date, idx: number) => {
                                                    const dateStr = day.toISOString().split('T')[0];
                                                    const dateShifts = summary[dateStr]?.shifts ?? {};
                                                    const dayEntries = Object.entries(dateShifts) as [string, ShiftTypeSummary][];

                                                    const fruehEntry = dayEntries.find(([abbr]) => abbr === 'F');
                                                    const zwischenEntry = dayEntries.find(([abbr]) => abbr === 'Z');
                                                    const spaetEntry = dayEntries.find(([abbr]) => abbr === 'S');
                                                    const nachtEntry = dayEntries.find(([abbr]) => abbr === 'N');

                                                    const fruehStr = fruehEntry ? generateSummaryString(fruehEntry) : 'F0|H0|A0';
                                                    const zwischenStr = zwischenEntry ? generateSummaryString(zwischenEntry) : 'F0|H0|A0';
                                                    const spaetStr = spaetEntry ? generateSummaryString(spaetEntry) : 'F0|H0|A0';
                                                    const nachtStr = nachtEntry ? generateSummaryString(nachtEntry) : 'F0|H0|A0';

                                                    return (
                                                        <td
                                                            key={`plan-${schedule.scheduleId}-day-${idx}`}
                                                            className={cn('sticky bottom-0 border-b border-border p-1 text-center text-sm bg-background')}
                                                        >
                                                            <div
                                                                className="text-xs text-muted-foreground">{fruehStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">{zwischenStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">{spaetStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">{nachtStr || '—'}</div>
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        );
                                    })}
                                    </tfoot>
                                </table>
                            </div>
                        </TooltipProvider>
                    ) :
                    (
                        <TooltipProvider delayDuration={300} skipDelayDuration={100}>
                            <div className={cn(
                                "relative overflow-auto",
                                isFullscreen ? "flex-1" : "max-h-[800px]"
                            )}>
                                <table className="w-full border-collapse text-sm">
                                    <thead className="sticky top-0 z-20 bg-card">
                                    <tr>
                                        <th className="sticky left-0 z-30 min-w-40 border-b border-r border-border bg-card p-3 text-left font-semibold text-foreground">
                                            Employee / Dienstplan
                                        </th>
                                        {days.map((day: Date, idx: number) => (
                                            <th
                                                key={idx}
                                                className={cn(
                                                    'border-b border-border p-3 text-center font-medium text-foreground min-w-[100px]',
                                                    isWeekend(day) && 'bg-muted/30'
                                                )}
                                            >
                                                <div className="space-y-1">
                                                    <div className="font-semibold">
                                                        {day.toLocaleDateString('de-DE', {
                                                            month: 'short',
                                                            day: 'numeric'
                                                        })}
                                                    </div>
                                                    <div className="text-xs text-muted-foreground">
                                                        {day.toLocaleDateString('de-DE', {weekday: 'short'})}
                                                    </div>
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                    </thead>
                                    <tbody>
                                    {groupedEmployees.map((group, groupIdx) => (
                                        <React.Fragment key={`group-${group[0]?.employee.id || groupIdx}`}>
                                            {group.map((item, itemIdx) => {
                                                const {employee, scheduleId, description, scheduleData} = item;
                                                const stats = getEmployeeStats(employee, scheduleData.days, scheduleData.shifts, scheduleData.variables);
                                                const isFirstInGroup = itemIdx === 0;
                                                const isLastInGroup = itemIdx === group.length - 1;

                                                return (
                                                    <tr
                                                        key={`${employee.id}-${scheduleId}`}
                                                        className={cn(
                                                            "transition-colors",
                                                            !isLastInGroup && "border-b-0"
                                                        )}
                                                    >
                                                        <td
                                                            className={cn(
                                                                'sticky left-0 z-20 border-r border-border p-3',
                                                                stats.hasOvertime
                                                                    ? 'bg-red-50 dark:bg-red-950/40'
                                                                    : 'bg-card',
                                                                isLastInGroup ? 'border-b' : 'border-b-0'
                                                            )}
                                                        >
                                                            <div className="space-y-1">
                                                                {isFirstInGroup && (
                                                                    <>
                                                                        <div
                                                                            className="font-medium text-foreground">{employee.name}</div>
                                                                        <div
                                                                            className="text-xs text-muted-foreground">{employee.level}</div>
                                                                    </>
                                                                )}
                                                                <div
                                                                    className={cn("text-xs font-semibold", isFirstInGroup && "mt-2", "text-blue-600 dark:text-blue-400")}>
                                                                    {description || "Ohne Beschreibung"}
                                                                </div>
                                                                <div className="text-xs">
                                                                    <div
                                                                        className="text-muted-foreground">{stats.totalShifts} Schichten
                                                                    </div>
                                                                    <div
                                                                        className={cn(
                                                                            'font-medium',
                                                                            stats.hasOvertime ? 'text-destructive' : 'text-muted-foreground'
                                                                        )}
                                                                    >
                                                                        {stats.actualHours.toFixed(1)}h
                                                                        / {stats.targetHours.toFixed(1)}h
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        {scheduleData.days.map((day: Date, dayIdx: number) => {
                                                            const shiftsForCell = getShiftsForCell(employee.id, day, scheduleData.shifts, scheduleData.variables);
                                                            const dateStr = day.toISOString().split('T')[0];
                                                            const cellKey = `${employee.id}-${scheduleId}-${dateStr}`;

                                                            const isDayOffFulfilled = scheduleData.fulfilledDayOffCells.has(`${employee.id}-${dateStr}`);
                                                            const isShiftWishFulfilled = scheduleData.fulfilledShiftWishCells.has(`${employee.id}-${dateStr}`);
                                                            const hasDayOffWish = scheduleData.allDayOffWishCells.has(`${employee.id}-${dateStr}`);
                                                            const shiftWishColors = scheduleData.allShiftWishColors[`${employee.id}-${dateStr}`] || [];

                                                            const isUnavailable = unavailable(employee, dayIdx + 1);

                                                            return (
                                                                <td
                                                                    key={dayIdx}
                                                                    className={cn(
                                                                        'p-2 text-center relative z-0 cursor-pointer hover:bg-foreground/5',
                                                                        isWeekend(day) && 'bg-muted/30 hover:bg-muted/90',
                                                                        isDayOffFulfilled && 'bg-amber-400/10 hover:bg-amber-400/25',
                                                                        isShiftWishFulfilled && 'bg-emerald-400/10 hover:bg-emerald-400/25',
                                                                        isUnavailable && 'bg-rose-400/10 hover:bg-rose-400/25',
                                                                        !shiftsForCell.length && !isDayOffFulfilled && hasDayOffWish && 'bg-rose-400/5 hover:bg-rose-400/20',
                                                                        isLastInGroup ? 'border-b border-border' : 'border-b-0'
                                                                    )}
                                                                    onMouseLeave={() => handleMouseLeave()}
                                                                    onClick={() => handleCellClick(cellKey)}
                                                                >
                                                                    {shiftsForCell.length > 0 ? (
                                                                        <div className="flex flex-col w-full gap-1">
                                                                            {shiftsForCell.map((shift) => (
                                                                                <div
                                                                                    key={shift.id}
                                                                                    className="rounded-md px-2 py-1.5 font-medium text-white w-full"
                                                                                    style={{backgroundColor: shift.color}}
                                                                                >
                                                                                    {shift.name}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <div className="py-1.5"/>
                                                                    )}

                                                                    {openTooltipCell === cellKey && (
                                                                        <Tooltip open={true}>
                                                                            <TooltipTrigger asChild>
                                                                                <div
                                                                                    className="absolute inset-0 top-8"/>
                                                                            </TooltipTrigger>
                                                                            <TooltipContent container={portalContainer}>
                                                                                <div className="text-sm space-y-1">
                                                                                    {shiftsForCell.length > 0 && (
                                                                                        <div className="space-y-1">
                                                                                            {shiftsForCell.map((shift) => (
                                                                                                <div key={shift.id}>
                                                                                                    <p className="font-semibold">{shift.name}</p>
                                                                                                    <p className="text-xs text-muted-foreground">
                                                                                                        Dauer: {Math.floor(shift.duration / 60)}h {shift.duration % 60}min
                                                                                                    </p>
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            </TooltipContent>
                                                                        </Tooltip>
                                                                    )}
                                                                </td>
                                                            );
                                                        })}
                                                    </tr>
                                                );
                                            })}
                                        </React.Fragment>
                                    ))}
                                    </tbody>
                                    <tfoot className="sticky bottom-0 bg-card z-30">
                                    {/* Per-Plan summary rows: render one summary row per schedule (stacked) */}
                                    {(props as CompareScheduleTableProps).schedules.map((schedule) => {
                                        const summary = scheduleSummaries[schedule.scheduleId] || {};
                                        return (
                                            <tr key={`summary-${schedule.scheduleId}`} className="border-t">
                                                <td className="sticky bottom-0 left-0 z-30 min-w-40 border-b border-r border-border bg-card p-3 text-left font-semibold text-foreground">
                                                    {schedule.description || `Plan ${schedule.scheduleId}`}
                                                </td>
                                                {schedule.days.map((day: Date, idx: number) => {
                                                    const dateStr = day.toISOString().split('T')[0];
                                                    const dateShifts = summary[dateStr]?.shifts ?? {};
                                                    const dayEntries = Object.entries(dateShifts) as [string, ShiftTypeSummary][];

                                                    const fruehEntry = dayEntries.find(([abbr]) => abbr === 'F');
                                                    const zwischenEntry = dayEntries.find(([abbr]) => abbr === 'Z');
                                                    const spaetEntry = dayEntries.find(([abbr]) => abbr === 'S');
                                                    const nachtEntry = dayEntries.find(([abbr]) => abbr === 'N');

                                                    const fruehStr = fruehEntry ? generateSummaryString(fruehEntry) : 'F0|H0|A0';
                                                    const zwischenStr = zwischenEntry ? generateSummaryString(zwischenEntry) : 'F0|H0|A0';
                                                    const spaetStr = spaetEntry ? generateSummaryString(spaetEntry) : 'F0|H0|A0';
                                                    const nachtStr = nachtEntry ? generateSummaryString(nachtEntry) : 'F0|H0|A0';

                                                    return (
                                                        <td
                                                            key={`plan-${schedule.scheduleId}-day-${idx}`}
                                                            className={cn('sticky bottom-0 border-b border-border p-2 text-center text-sm min-w-[100px] bg-background')}
                                                        >
                                                            <div
                                                                className="text-xs text-muted-foreground">F: {fruehStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">Z: {zwischenStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">S: {spaetStr || '—'}</div>
                                                            <div
                                                                className="text-xs text-muted-foreground">N: {nachtStr || '—'}</div>
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        );
                                    })}
                                    </tfoot>
                                </table>
                            </div>
                        </TooltipProvider>
                    )
            ) : filteredEmployees.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    Keine Mitarbeiter gefunden.
                </div>
            ) : reducedView ?
                (
                    <TooltipProvider delayDuration={300} skipDelayDuration={100}>
                        <div className={cn(
                            "relative overflow-auto",
                            isFullscreen ? "flex-1" : "max-h-[800px]"
                        )}>
                            <table className="w-full border-collapse text-sm">
                                <thead className="sticky top-0 z-20 bg-card">
                                <tr>
                                    <th className="sticky left-0 z-30 border-b border-r border-border bg-card p-1 text-left font-semibold text-foreground">
                                        Employee
                                    </th>
                                    {days.map((day: Date, idx: number) => (
                                        <th
                                            key={idx}
                                            className={cn(
                                                'border-b border-border text-center font-medium text-foreground',
                                                isWeekend(day) && 'bg-muted/30'
                                            )}
                                        >
                                            <div className="font-semibold">
                                                {day.toLocaleDateString('de-DE', {month: 'numeric', day: 'numeric'})}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {day.toLocaleDateString('de-DE', {weekday: 'short'})}
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                                </thead>
                                <tbody>
                                {filteredEmployees.map((employee: ScheduleEmployee) => {
                                    const stats = getEmployeeStats(employee, days, shifts, variables);
                                    return (
                                        <tr key={employee.id} className="transition-colors">
                                            <td
                                                className={cn(
                                                    'sticky left-0 z-20 border-b border-r border-border p-1',
                                                    stats.hasOvertime
                                                        ? 'bg-red-50 dark:bg-red-950/40'
                                                        : 'bg-card'
                                                )}
                                            >
                                                <div className="font-medium text-foreground">{employee.name}</div>
                                                <div className="text-xs text-foreground">{employee.level[0]} -
                                                    <span
                                                        className={cn(
                                                            'font-medium',
                                                            stats.hasOvertime ? 'text-destructive' : 'text-muted-foreground'
                                                        )}
                                                    >
                            {stats.actualHours.toFixed(1)}h / {stats.targetHours.toFixed(1)}h
                          </span>
                                                </div>
                                            </td>
                                            {days.map((day: Date, dayIdx: number) => {
                                                const shiftsForCell = getShiftsForCell(employee.id, day, shifts, variables);
                                                const dateStr = day.toISOString().split('T')[0];
                                                const cellKey = `${employee.id}-${dateStr}`;

                                                const isDayOffFulfilled = fulfilledDayOffCells.has(cellKey);
                                                const isShiftWishFulfilled = fulfilledShiftWishCells.has(cellKey);
                                                const hasDayOffWish = allDayOffWishCells.has(cellKey);
                                                const shiftWishColors = allShiftWishColors[cellKey] || [];

                                                const isUnavailable = unavailable(employee, dayIdx + 1);

                                                return (
                                                    <td
                                                        key={dayIdx}
                                                        className={cn(
                                                            // Default cell state when no other status color applies.
                                                            'border-b border-border px-2 text-center relative z-0 cursor-pointer hover:bg-foreground/5',

                                                            // Weekends use a slightly darker hover state.
                                                            isWeekend(day) && 'bg-muted/30 hover:bg-muted/90',

                                                            // Fulfilled day-off wishes stay amber and intensify on hover.
                                                            isDayOffFulfilled && 'bg-amber-400/10 hover:bg-amber-400/25',

                                                            // Fulfilled shift wishes stay emerald and intensify on hover.
                                                            isShiftWishFulfilled && 'bg-emerald-400/10 hover:bg-emerald-400/25',

                                                            // Unavailable days stay rose and intensify on hover.
                                                            isUnavailable && 'bg-rose-400/10 hover:bg-rose-400/25',

                                                            // Unfulfilled day-off wishes keep a lighter rose highlight.
                                                            !shiftsForCell.length && !isDayOffFulfilled && hasDayOffWish && 'bg-rose-400/5 hover:bg-rose-400/20'
                                                        )}
                                                        onMouseLeave={() => handleMouseLeave()}
                                                        onClick={() => handleCellClick(cellKey)}
                                                    >
                                                        {shiftsForCell.length > 0 || hasDayOffWish || shiftWishColors.length > 0 || shifts.some((s: Shift) => unavailable(employee, dayIdx + 1, s)) ? (
                                                            <>
                                                                <div className="flex flex-col items-center gap-1">
                                                                    {/* RENDER ALL SHIFTS FOR THIS CELL */}
                                                                    {shiftsForCell.length > 0 ? (
                                                                        <div className="flex flex-col w-full gap-1">
                                                                            {shiftsForCell.map((shift) => (
                                                                                <div
                                                                                    key={shift.id}
                                                                                    className="rounded-md px-2 py-1.5 font-medium text-white"
                                                                                    style={{backgroundColor: shift.color}}
                                                                                >
                                                                                    {shift.abbreviation}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <div className="py-1.5"/>
                                                                    )}
                                                                </div>
                                                                {openTooltipCell === cellKey && (
                                                                    <Tooltip open={true}>
                                                                        <TooltipTrigger asChild>
                                                                            <div className="absolute inset-0 top-8"/>
                                                                        </TooltipTrigger>
                                                                        <TooltipContent container={portalContainer}>
                                                                            <div className="text-sm space-y-1">
                                                                                {shiftsForCell.length > 0 && (
                                                                                    <div className="space-y-1">
                                                                                        {shiftsForCell.map((shift) => (
                                                                                            <div key={shift.id}>
                                                                                                <p className="font-semibold">{shift.name}</p>
                                                                                                <p className="text-xs text-muted-foreground">
                                                                                                    Dauer: {Math.floor(shift.duration / 60)}h {shift.duration % 60}min
                                                                                                </p>
                                                                                            </div>
                                                                                        ))}
                                                                                    </div>
                                                                                )}
                                                                                {(hasDayOffWish || shiftWishColors.length > 0 || shifts.some((s: Shift) => unavailable(employee, dayIdx + 1, s))) && shiftsForCell.length > 0 && (
                                                                                    <div
                                                                                        className="border-t border-border pt-1 mt-1"/>
                                                                                )}
                                                                                {shifts.filter((s: Shift) => unavailable(employee, dayIdx + 1, s)).map((s: Shift) => (
                                                                                    <p key={s.id} className="text-xs">●
                                                                                        Blockiert: {s.name}</p>
                                                                                ))}
                                                                                {hasDayOffWish && (
                                                                                    <p className="text-xs">△ Wunsch:
                                                                                        Freier Tag</p>
                                                                                )}
                                                                                {shiftWishColors.map((color: string, idx: number) => {
                                                                                    const shiftForColor = shifts.find((s: Shift) => s.color === color);
                                                                                    return (
                                                                                        <p key={idx}
                                                                                           className="text-xs">
                                                                                            ◆
                                                                                            Schichtwunsch: {shiftForColor?.name || 'Unbekannt'}
                                                                                        </p>
                                                                                    );
                                                                                })}
                                                                            </div>
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                )}
                                                            </>
                                                        ) : (
                                                            <div className="flex flex-col items-center gap-1">
                                                                {/* RENDER ALL SHIFTS FOR THIS CELL */}
                                                                {shiftsForCell.length > 0 ? (
                                                                    <div className="flex flex-col w-full gap-1">
                                                                        {shiftsForCell.map((shift) => (
                                                                            <div
                                                                                key={shift.id}
                                                                                className="rounded-md px-2 py-1.5 font-medium text-white w-full"
                                                                                style={{backgroundColor: shift.color}}
                                                                            >
                                                                                {shift.name}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <div className="py-1.5"/>
                                                                )}
                                                            </div>
                                                        )}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    );
                                })}
                                <tr>
                                    <td className="sticky bottom-0 left-0 z-30 border-b border-r border-border bg-card text-left font-semibold text-foreground">
                                        <div className="flex items-center justify-between">
                                            <div className="whitespace-nowrap">Gesamtbelegung</div>
                                            <div className="text-xs text-muted-foreground flex pr-2 flex-col items-end">
                                                <div>F</div>
                                                <div>Z</div>
                                                <div>S</div>
                                                <div>N</div>
                                            </div>
                                        </div>
                                    </td>
                                    {days.map((day: Date, idx: number) => {
                                        const dateStr = day.toISOString().split('T')[0];
                                        const dateShifts = shiftSummary?.[dateStr]?.shifts ?? {};
                                        const dayEntries = Object.entries(dateShifts) as [string, ShiftTypeSummary][]; // typed entries

                                        const fruehEntry = dayEntries.find(([abbr]) => abbr === 'F');
                                        const zwischenEntry = dayEntries.find(([abbr]) => abbr === 'Z');
                                        const spaetEntry = dayEntries.find(([abbr]) => abbr === 'S');
                                        const nachtEntry = dayEntries.find(([abbr]) => abbr === 'N');

                                        const fruehStr = fruehEntry ? generateSummaryString(fruehEntry) : 'F0|H0|A0';
                                        const zwischenStr = zwischenEntry ? generateSummaryString(zwischenEntry) : 'F0|H0|A0';
                                        const spaetStr = spaetEntry ? generateSummaryString(spaetEntry) : 'F0|H0|A0';
                                        const nachtStr = nachtEntry ? generateSummaryString(nachtEntry) : 'F0|H0|A0';

                                        return (
                                            <td
                                                key={`total-single-${idx}`}
                                                className={cn('sticky bottom-0 border-b border-border p-1 text-center text-sm bg-background', isWeekend(day))}
                                            >
                                                <div className="text-xs text-muted-foreground">{fruehStr || '—'}</div>
                                                <div
                                                    className="text-xs text-muted-foreground">{zwischenStr || '—'}</div>
                                                <div className="text-xs text-muted-foreground">{spaetStr || '—'}</div>
                                                <div className="text-xs text-muted-foreground">{nachtStr || '—'}</div>
                                            </td>
                                        );
                                    })}
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    </TooltipProvider>
                )
                : (
                    <TooltipProvider delayDuration={300} skipDelayDuration={100}>
                        <div className={cn(
                            "relative overflow-auto",
                            isFullscreen ? "flex-1" : "max-h-[800px]"
                        )}>
                            <table className="w-full border-collapse text-sm">
                                <thead className="sticky top-0 z-20 bg-card">
                                <tr>
                                    <th className="sticky left-0 z-30 min-w-40 border-b border-r border-border bg-card p-3 text-left font-semibold text-foreground">
                                        Employee
                                    </th>
                                    {days.map((day: Date, idx: number) => (
                                        <th
                                            key={idx}
                                            className={cn(
                                                'border-b border-border p-3 text-center font-medium text-foreground min-w-[100px]',
                                                isWeekend(day) && 'bg-muted/30'
                                            )}
                                        >
                                            <div className="space-y-1">
                                                <div className="font-semibold">
                                                    {day.toLocaleDateString('de-DE', {month: 'short', day: 'numeric'})}
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    {day.toLocaleDateString('de-DE', {weekday: 'short'})}
                                                </div>
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                                </thead>
                                <tbody>
                                {filteredEmployees.map((employee: ScheduleEmployee) => {
                                    const stats = getEmployeeStats(employee, days, shifts, variables);
                                    return (
                                        <tr key={employee.id} className="transition-colors">
                                            <td
                                                className={cn(
                                                    'sticky left-0 z-20 border-b border-r border-border p-3',
                                                    stats.hasOvertime
                                                        ? 'bg-red-50 dark:bg-red-950/40'
                                                        : 'bg-card'
                                                )}
                                            >
                                                <div className="space-y-1">
                                                    <div className="font-medium text-foreground">{employee.name}</div>
                                                    <div
                                                        className="text-xs text-muted-foreground">{employee.level}</div>
                                                    <div className="mt-2 text-xs">
                                                        <div
                                                            className="text-muted-foreground">{stats.totalShifts} Schichten
                                                        </div>
                                                        <div
                                                            className={cn(
                                                                'font-medium',
                                                                stats.hasOvertime ? 'text-destructive' : 'text-muted-foreground'
                                                            )}
                                                        >
                                                            {stats.actualHours.toFixed(1)}h
                                                            / {stats.targetHours.toFixed(1)}h
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            {days.map((day: Date, dayIdx: number) => {
                                                const shiftsForCell = getShiftsForCell(employee.id, day, shifts, variables);
                                                const dateStr = day.toISOString().split('T')[0];
                                                const cellKey = `${employee.id}-${dateStr}`;

                                                const isDayOffFulfilled = fulfilledDayOffCells.has(cellKey);
                                                const isShiftWishFulfilled = fulfilledShiftWishCells.has(cellKey);
                                                const hasDayOffWish = allDayOffWishCells.has(cellKey);
                                                const shiftWishColors = allShiftWishColors[cellKey] || [];

                                                const isUnavailable = unavailable(employee, dayIdx + 1);

                                                return (
                                                    <td
                                                        key={dayIdx}
                                                        className={cn(
                                                            // Default cell state when no other status color applies.
                                                            'border-b border-border p-2 text-center relative z-0 cursor-pointer hover:bg-foreground/5',

                                                            // Weekends use a slightly darker hover state.
                                                            isWeekend(day) && 'bg-muted/30 hover:bg-muted/90',

                                                            // Fulfilled day-off wishes stay amber and intensify on hover.
                                                            isDayOffFulfilled && 'bg-amber-400/10 hover:bg-amber-400/25',

                                                            // Fulfilled shift wishes stay emerald and intensify on hover.
                                                            isShiftWishFulfilled && 'bg-emerald-400/10 hover:bg-emerald-400/25',

                                                            // Unavailable days stay rose and intensify on hover.
                                                            isUnavailable && 'bg-rose-400/10 hover:bg-rose-400/25',

                                                            // Unfulfilled day-off wishes keep a lighter rose highlight.
                                                            !shiftsForCell.length && !isDayOffFulfilled && hasDayOffWish && 'bg-rose-400/5 hover:bg-rose-400/20'
                                                        )}
                                                        onMouseLeave={() => handleMouseLeave()}
                                                        onClick={() => handleCellClick(cellKey)}
                                                    >
                                                        {shiftsForCell.length > 0 || hasDayOffWish || shiftWishColors.length > 0 || shifts.some((s: Shift) => unavailable(employee, dayIdx + 1, s)) ? (
                                                            <>
                                                                <div
                                                                    className="flex flex-col items-center gap-1 w-full">
                                                                    {/* unavailable shift circles */}
                                                                    <div className="flex items-center gap-1 mb-1">
                                                                        {shifts.map((s: Shift) =>
                                                                            unavailable(employee, dayIdx + 1, s) ? (
                                                                                <div
                                                                                    key={s.id}
                                                                                    className="w-2 h-2 rounded-full"
                                                                                    style={{backgroundColor: s.color}}
                                                                                />
                                                                            ) : null
                                                                        )}
                                                                    </div>

                                                                    {/* day-off wish + shift wish icons */}
                                                                    <div className="flex items-center gap-1 mb-1">
                                                                        {hasDayOffWish && (
                                                                            <div
                                                                                className="w-0 h-0 border-l-4 border-r-4 border-b-[6px]"
                                                                                style={{
                                                                                    borderLeftColor: 'transparent',
                                                                                    borderRightColor: 'transparent',
                                                                                    borderBottomColor: '#b77c02',
                                                                                }}
                                                                            />
                                                                        )}
                                                                        {shiftWishColors.map((color: string, idx: number) => (
                                                                            <div
                                                                                key={idx}
                                                                                className="w-2 h-2"
                                                                                style={{
                                                                                    backgroundColor: color,
                                                                                    transform: 'rotate(45deg)',
                                                                                }}
                                                                            />
                                                                        ))}
                                                                    </div>

                                                                    {/* RENDER ALL SHIFTS FOR THIS CELL */}
                                                                    {shiftsForCell.length > 0 ? (
                                                                        <div className="flex flex-col w-full gap-1">
                                                                            {shiftsForCell.map((shift) => (
                                                                                <div
                                                                                    key={shift.id}
                                                                                    className="rounded-md px-2 py-1.5 font-medium text-white w-full"
                                                                                    style={{backgroundColor: shift.color}}
                                                                                >
                                                                                    {shift.name}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <div className="py-1.5"/>
                                                                    )}
                                                                </div>
                                                                {openTooltipCell === cellKey && (
                                                                    <Tooltip open={true}>
                                                                        <TooltipTrigger asChild>
                                                                            <div className="absolute inset-0 top-8"/>
                                                                        </TooltipTrigger>
                                                                        <TooltipContent container={portalContainer}>
                                                                            <div className="text-sm space-y-1">
                                                                                {shiftsForCell.length > 0 && (
                                                                                    <div className="space-y-1">
                                                                                        {shiftsForCell.map((shift) => (
                                                                                            <div key={shift.id}>
                                                                                                <p className="font-semibold">{shift.name}</p>
                                                                                                <p className="text-xs text-muted-foreground">
                                                                                                    Dauer: {Math.floor(shift.duration / 60)}h {shift.duration % 60}min
                                                                                                </p>
                                                                                            </div>
                                                                                        ))}
                                                                                    </div>
                                                                                )}
                                                                                {(hasDayOffWish || shiftWishColors.length > 0 || shifts.some((s: Shift) => unavailable(employee, dayIdx + 1, s))) && shiftsForCell.length > 0 && (
                                                                                    <div
                                                                                        className="border-t border-border pt-1 mt-1"/>
                                                                                )}
                                                                                {shifts.filter((s: Shift) => unavailable(employee, dayIdx + 1, s)).map((s: Shift) => (
                                                                                    <p key={s.id} className="text-xs">●
                                                                                        Blockiert: {s.name}</p>
                                                                                ))}
                                                                                {hasDayOffWish && (
                                                                                    <p className="text-xs">△ Wunsch:
                                                                                        Freier Tag</p>
                                                                                )}
                                                                                {shiftWishColors.map((color: string, idx: number) => {
                                                                                    const shiftForColor = shifts.find((s: Shift) => s.color === color);
                                                                                    return (
                                                                                        <p key={idx}
                                                                                           className="text-xs">
                                                                                            ◆
                                                                                            Schichtwunsch: {shiftForColor?.name || 'Unbekannt'}
                                                                                        </p>
                                                                                    );
                                                                                })}
                                                                            </div>
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                )}
                                                            </>
                                                        ) : (
                                                            <div className="flex flex-col items-center gap-1">
                                                                {/* unavailable shift circles */}
                                                                <div className="flex items-center gap-1 mb-1">
                                                                    {shifts.map((s: Shift) =>
                                                                        unavailable(employee, dayIdx + 1, s) ? (
                                                                            <div
                                                                                key={s.id}
                                                                                className="w-2 h-2 rounded-full"
                                                                                style={{backgroundColor: s.color}}
                                                                            />
                                                                        ) : null
                                                                    )}
                                                                </div>

                                                                {/* day-off wish + shift wish icons */}
                                                                <div className="flex items-center gap-1 mb-1">
                                                                    {hasDayOffWish && (
                                                                        <div
                                                                            className="w-0 h-0 border-l-4 border-r-4 border-b-[6px]"
                                                                            style={{
                                                                                borderLeftColor: 'transparent',
                                                                                borderRightColor: 'transparent',
                                                                                borderBottomColor: '#b77c02',
                                                                            }}
                                                                        />
                                                                    )}
                                                                    {shiftWishColors.map((color, idx) => (
                                                                        <div
                                                                            key={idx}
                                                                            className="w-2 h-2"
                                                                            style={{
                                                                                backgroundColor: color,
                                                                                transform: 'rotate(45deg)',
                                                                            }}
                                                                        />
                                                                    ))}
                                                                </div>

                                                                {/* RENDER ALL SHIFTS FOR THIS CELL */}
                                                                {shiftsForCell.length > 0 ? (
                                                                    <div className="flex flex-col w-full gap-1">
                                                                        {shiftsForCell.map((shift) => (
                                                                            <div
                                                                                key={shift.id}
                                                                                className="rounded-md px-2 py-1.5 font-medium text-white w-full"
                                                                                style={{backgroundColor: shift.color}}
                                                                            >
                                                                                {shift.name}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <div className="py-1.5"/>
                                                                )}
                                                            </div>
                                                        )}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    );
                                })}
                                <tr>
                                    <td className="sticky bottom-0 left-0 z-30 min-w-40 border-b border-r border-border bg-card p-3 text-left font-semibold text-foreground">
                                        Gesamtbelegung
                                    </td>
                                    {days.map((day: Date, idx: number) => {
                                        const dateStr = day.toISOString().split('T')[0];
                                        const dateShifts = shiftSummary?.[dateStr]?.shifts ?? {};
                                        const dayEntries = Object.entries(dateShifts) as [string, ShiftTypeSummary][]; // typed entries

                                        const fruehEntry = dayEntries.find(([abbr]) => abbr === 'F');
                                        const zwischenEntry = dayEntries.find(([abbr]) => abbr === 'Z');
                                        const spaetEntry = dayEntries.find(([abbr]) => abbr === 'S');
                                        const nachtEntry = dayEntries.find(([abbr]) => abbr === 'N');

                                        const fruehStr = fruehEntry ? generateSummaryString(fruehEntry) : 'F0|H0|A0';
                                        const zwischenStr = zwischenEntry ? generateSummaryString(zwischenEntry) : 'F0|H0|A0';
                                        const spaetStr = spaetEntry ? generateSummaryString(spaetEntry) : 'F0|H0|A0';
                                        const nachtStr = nachtEntry ? generateSummaryString(nachtEntry) : 'F0|H0|A0';

                                        return (
                                            <td
                                                key={`total-single-${idx}`}
                                                className={cn('sticky bottom-0 border-b border-border p-2 text-center text-sm min-w-[100px] bg-background', isWeekend(day))}
                                            >
                                                <div
                                                    className="text-xs text-muted-foreground">F: {fruehStr || '—'}</div>
                                                <div
                                                    className="text-xs text-muted-foreground">Z: {zwischenStr || '—'}</div>
                                                <div
                                                    className="text-xs text-muted-foreground">S: {spaetStr || '—'}</div>
                                                <div
                                                    className="text-xs text-muted-foreground">N: {nachtStr || '—'}</div>
                                            </td>
                                        );
                                    })}
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    </TooltipProvider>
                )}

        </div>
    );
}
