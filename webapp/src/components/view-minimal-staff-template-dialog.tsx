'use client';

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';
import {Clock, Moon, Sun, Sunrise} from 'lucide-react';
import {
    EmployeeCategory,
    MinimalStaffRequirements,
    ShiftType,
    WeekDay
} from '@/entities/models/minimal-staff.model';
import {cn} from '@/lib/utils';

interface ViewMinimalStaffTemplateDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    template: {
        description: string;
        content: MinimalStaffRequirements;
        last_modified: string;
    } | null;
}

const weekDays: { key: WeekDay; label: string; isWeekend: boolean }[] = [
    {key: 'Mo', label: 'Montag', isWeekend: false},
    {key: 'Di', label: 'Dienstag', isWeekend: false},
    {key: 'Mi', label: 'Mittwoch', isWeekend: false},
    {key: 'Do', label: 'Donnerstag', isWeekend: false},
    {key: 'Fr', label: 'Freitag', isWeekend: false},
    {key: 'Sa', label: 'Samstag', isWeekend: true},
    {key: 'So', label: 'Sonntag', isWeekend: true},
];

const shifts: { key: ShiftType; label: string; icon: React.ReactNode; color: string }[] = [
    {key: 'F', label: 'Frühdienst', icon: <Sunrise className="h-4 w-4"/>, color: 'text-amber-600'},
    {key: 'Z', label: 'Zwischendienst', icon: <Clock className="h-4 w-4"/>, color: 'text-cyan-600'},
    {key: 'S', label: 'Spätdienst', icon: <Sun className="h-4 w-4"/>, color: 'text-orange-600'},
    {key: 'N', label: 'Nachtdienst', icon: <Moon className="h-4 w-4"/>, color: 'text-blue-600'},
];

const categories: { key: EmployeeCategory; label: string; color: string }[] = [
    {key: 'Fachkraft', label: 'Fachkraft', color: 'bg-blue-500'},
    {key: 'Azubi', label: 'Azubi', color: 'bg-green-500'},
    {key: 'Hilfskraft', label: 'Hilfskraft', color: 'bg-purple-500'},
];

/**
 * Dialog for previewing a minimal staff template without loading it.
 */
export function ViewMinimalStaffTemplateDialog({
                                                   open,
                                                   onOpenChange,
                                                   template,
                                               }: ViewMinimalStaffTemplateDialogProps) {
    if (!template) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[95vw] min-w-[60vw] w-full sm:max-w-[50vw] max-h-[90vh]">
                <DialogHeader>
                    <DialogTitle>Template-Vorschau</DialogTitle>
                    <DialogDescription>{template.description}</DialogDescription>
                </DialogHeader>

                <ScrollArea className="max-h-[500px] pr-4">
                    <Tabs defaultValue="Fachkraft" className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                            {categories.map(({key, label, color}) => (
                                <TabsTrigger key={key} value={key} className="gap-2">
                                    <div className={cn('w-3 h-3 rounded-full', color)}/>
                                    {label}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        {categories.map(({key: category, label, color}) => (
                            <TabsContent key={category} value={category} className="mt-4">
                                <div className="rounded-md border">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead className="w-[160px]">Wochentag</TableHead>
                                                {shifts.map(({key, label: shiftLabel, icon, color: shiftColor}) => (
                                                    <TableHead key={key} className="text-center">
                                                        <div className="flex items-center justify-center gap-1">
                                                            <span className={shiftColor}>{icon}</span>
                                                            <span className="hidden sm:inline">{shiftLabel}</span>
                                                            <span className="sm:hidden">{key}</span>
                                                        </div>
                                                    </TableHead>
                                                ))}
                                                <TableHead className="text-center">Gesamt</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {weekDays.map(({key: day, label: dayLabel, isWeekend}) => {
                                                const dayReqs = template.content[category][day];
                                                const total = dayReqs.F + dayReqs.Z + dayReqs.S + dayReqs.N;
                                                return (
                                                    <TableRow key={day} className={cn(isWeekend && 'bg-muted/30')}>
                                                        <TableCell className="font-medium">
                                                            <div className="flex items-center gap-2">
                                                                <span>{dayLabel}</span>
                                                                {isWeekend && (
                                                                    <Badge variant="outline" className="text-xs">
                                                                        WE
                                                                    </Badge>
                                                                )}
                                                            </div>
                                                        </TableCell>
                                                        {shifts.map(({key: shift}) => (
                                                            <TableCell key={shift} className="text-center">
                                                                <Badge variant="secondary"
                                                                       className="font-mono w-10 justify-center">
                                                                    {dayReqs[shift]}
                                                                </Badge>
                                                            </TableCell>
                                                        ))}
                                                        <TableCell className="text-center">
                                                            <Badge variant="secondary" className="font-mono">
                                                                {total}
                                                            </Badge>
                                                        </TableCell>
                                                    </TableRow>
                                                );
                                            })}
                                        </TableBody>
                                    </Table>
                                </div>
                            </TabsContent>
                        ))}
                    </Tabs>
                </ScrollArea>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Schließen
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
