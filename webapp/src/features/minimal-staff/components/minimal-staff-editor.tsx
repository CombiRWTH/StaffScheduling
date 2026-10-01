'use client';

import {useEffect, useState} from 'react';
import {
    EmployeeCategory,
    MinimalStaffRequirements,
    ShiftType,
    WeekDay
} from '@/entities/models/minimal-staff.model';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs';
import {Badge} from '@/components/ui/badge';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';
import {
    Clock,
    Moon,
    Save,
    // Save as SaveIcon,
    Sun,
    Sunrise,
    // Upload,
} from 'lucide-react';
import {cn} from '@/lib/utils';
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
import {SaveTemplateDialog} from '@/components/save-template-dialog';
import {ImportTemplateDialog} from '@/components/import-template-dialog';
import {
    createMinimalStaffTemplateAction,
    getMinimalStaffTemplateAction,
    listMinimalStaffTemplatesAction,
} from '@/features/templates/minimal-staff-templates.actions';
import {TemplateSummary} from '@/entities/models/template.model';
import {useSearchParams} from 'next/navigation';
import {toast} from 'sonner';

interface MinimalStaffEditorProps {
    requirements: MinimalStaffRequirements;
    onSave: (requirements: MinimalStaffRequirements) => void;
    isSaving?: boolean;
    caseId?: number;
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

const categories: { key: EmployeeCategory; label: string; color: string; description: string }[] = [
    {
        key: 'Fachkraft',
        label: 'Fachkraft',
        color: 'bg-blue-500',
        description: 'Qualifizierte Mitarbeiter mit abgeschlossener Ausbildung'
    },
    {
        key: 'Azubi',
        label: 'Azubi',
        color: 'bg-green-500',
        description: 'Auszubildende in der Berufsausbildung'
    },
    {
        key: 'Hilfskraft',
        label: 'Hilfskraft',
        color: 'bg-purple-500',
        description: 'Unterstützende Mitarbeiter ohne spezifische Qualifikation'
    },
];

export function MinimalStaffEditor({requirements, onSave, isSaving, caseId: caseIdProp}: MinimalStaffEditorProps) {
    const searchParams = useSearchParams();
    const caseId = caseIdProp ?? parseInt(searchParams.get('caseId') ?? '0', 10);
    const [localRequirements, setLocalRequirements] = useState<MinimalStaffRequirements>(requirements);
    const [hasChanges, setHasChanges] = useState(false);
    const [saveDialogOpen, setSaveDialogOpen] = useState(false);
    const [importDialogOpen, setImportDialogOpen] = useState(false);
    const [importConfirmOpen, setImportConfirmOpen] = useState(false);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
    const [templates, setTemplates] = useState<TemplateSummary[]>([]);
    const [isCreating, setIsCreating] = useState(false);

    // Fetch templates on mount
    useEffect(() => {
        if (!caseId) return;
        listMinimalStaffTemplatesAction(caseId)
            .then(setTemplates)
            .catch(() => setTemplates([]));
    }, [caseId]);

    const handleSaveAsTemplate = async (description: string) => {
        setIsCreating(true);
        const result = await createMinimalStaffTemplateAction(caseId, localRequirements, description);
        if (!result.success) {
            toast.error(result.error);
            setIsCreating(false);
            return;
        }
        setSaveDialogOpen(false);
        const updated = await listMinimalStaffTemplatesAction(caseId);
        setTemplates(updated);
        toast.success('Template gespeichert');
        setIsCreating(false);
    };

    const handleImportTemplate = (templateId: string) => {
        setSelectedTemplateId(templateId);
        setImportDialogOpen(false);
        setImportConfirmOpen(true);
    };

    const confirmImport = async () => {
        if (!selectedTemplateId) return;
        try {
            const result = await getMinimalStaffTemplateAction(caseId, selectedTemplateId);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setLocalRequirements(result.data.content);
            setHasChanges(true);
        } finally {
            setImportConfirmOpen(false);
            setSelectedTemplateId(null);
        }
    };

    // Sync local state when props change (only if user has no unsaved changes)
    useEffect(() => {
        if (!hasChanges) {
            const reqStr = JSON.stringify(requirements);
            const localStr = JSON.stringify(localRequirements);
            if (reqStr !== localStr) {
                Promise.resolve().then(() => setLocalRequirements(requirements));
            }
        }
    }, [requirements, hasChanges, localRequirements]);

    const handleValueChange = (
        category: EmployeeCategory,
        day: WeekDay,
        shift: ShiftType,
        value: string
    ) => {
        const numValue = Math.max(0, parseInt(value) || 0);
        setLocalRequirements(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [day]: {
                    ...prev[category][day],
                    [shift]: numValue,
                },
            },
        }));
        setHasChanges(true);
    };

    const handleSave = () => {
        onSave(localRequirements);
        setHasChanges(false);
    };

    const getTotalForDay = (category: EmployeeCategory, day: WeekDay) => {
        const dayReqs = localRequirements[category][day];
        return dayReqs.F + dayReqs.Z + dayReqs.S + dayReqs.N;
    };

    return (
        <div className="space-y-6">
            {/* Header with Save Button */}
            {/* Tabs for Categories */}
            <Tabs defaultValue="Fachkraft" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                    {categories.map(({key, label, color}) => (
                        <TabsTrigger key={key} value={key} className="gap-2">
                            <div className={cn("w-3 h-3 rounded-full", color)}/>
                            {label}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {categories.map(({key: category, label, color, description}) => (
                    <TabsContent key={category} value={category} className="space-y-4">
                        <Card>
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <CardTitle className="flex items-center gap-2">
                                            <div className={cn("w-4 h-4 rounded-full", color)}/>
                                            {label}
                                        </CardTitle>
                                        <p className="text-sm text-muted-foreground">{description}</p>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="rounded-md border">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead className="w-[180px]">Wochentag</TableHead>
                                                {shifts.map(({key, label, icon, color}) => (
                                                    <TableHead key={key} className="text-center">
                                                        <div className="flex items-center justify-center gap-2">
                                                            <span className={color}>{icon}</span>
                                                            <span className="hidden sm:inline">{label}</span>
                                                            <span className="sm:hidden">{key}</span>
                                                        </div>
                                                    </TableHead>
                                                ))}
                                                <TableHead className="text-center">Gesamt</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {weekDays.map(({key: day, label, isWeekend}) => (
                                                <TableRow key={day} className={cn(isWeekend && "bg-muted/30")}>
                                                    <TableCell className="font-medium">
                                                        <div className="flex items-center gap-2">
                                                            <span>{label}</span>
                                                            {isWeekend && (
                                                                <Badge variant="outline" className="text-xs">
                                                                    Wochenende
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    </TableCell>
                                                    {shifts.map(({key: shift}) => (
                                                        <TableCell key={shift}>
                                                            <div className="flex flex-col items-center">
                                                                <Input
                                                                    type="number"
                                                                    min="0"
                                                                    max="99"
                                                                    value={localRequirements[category][day][shift]}
                                                                    onChange={e => handleValueChange(category, day, shift, e.target.value)}
                                                                    className="w-20 text-center mx-auto"
                                                                />
                                                            </div>
                                                        </TableCell>
                                                    ))}
                                                    <TableCell className="text-center">
                                                        <Badge variant="secondary" className="font-mono">
                                                            {getTotalForDay(category, day)}
                                                        </Badge>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                            <TableRow key="total" className={cn("bg-muted/30")}>
                                                <TableCell className="font-medium">
                                                    <div className="flex items-center gap-2">
                                                        <span>Gesamt</span>
                                                    </div>
                                                </TableCell>
                                                {shifts.map(({key: shift}) => (
                                                    <TableCell key={shift}>
                                                        <div className="flex flex-col items-center">
                                                            <Badge variant="secondary" className="font-mono">
                                                                {weekDays.reduce((sum, {key: day}) => sum + localRequirements[category][day][shift], 0)}
                                                            </Badge>
                                                        </div>
                                                    </TableCell>

                                                ))}
                                                <TableCell className="text-center">
                                                    <Badge variant="secondary" className="font-mono">
                                                        {weekDays.reduce((sum, {key: day}) => sum + getTotalForDay(category, day), 0)}
                                                    </Badge>
                                                </TableCell>
                                            </TableRow>
                                        </TableBody>
                                    </Table>
                                </div>

                                {/* Legend */}
                                <div className="mt-4 pt-4 border-t">
                                    <p className="text-sm text-muted-foreground mb-2">Schichtzeiten:</p>
                                    <div className="flex flex-wrap gap-4">
                                        {shifts.map(({key, label, icon, color}) => (
                                            <div key={key} className="flex items-center gap-2 text-sm">
                                                <span className={color}>{icon}</span>
                                                <span className="font-medium">{key}:</span>
                                                <span className="text-muted-foreground">{label}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                ))}
            </Tabs>

            {/* Bottom Toolbar */}
            <div className="flex justify-between gap-2 pt-4 border-t">
                {/*
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={() => setImportDialogOpen(true)}
                        disabled={isSaving}
                        size="sm"
                    >
                        <Upload className="mr-2 h-4 w-4"/>
                        Template laden
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => setSaveDialogOpen(true)}
                        disabled={isSaving}
                        size="sm"
                    >
                        <SaveIcon className="mr-2 h-4 w-4"/>
                        Als Template speichern
                    </Button>
                </div>
                */}
                <div/>
                <Button onClick={handleSave} disabled={isSaving || !hasChanges} size="lg">
                    <Save className="h-4 w-4 mr-2"/>
                    {isSaving ? 'Speichert...' : hasChanges ? 'Änderungen speichern' : 'Gespeichert'}
                </Button>
            </div>

            <SaveTemplateDialog
                open={saveDialogOpen}
                onOpenChange={setSaveDialogOpen}
                onSave={handleSaveAsTemplate}
                isSaving={isCreating}
                title="Mindestbesetzung als Template speichern"
                descriptionPlaceholder="z.B. 'Standardbesetzung Sommer' oder 'Erhöhte Besetzung Wochenende'"
            />

            <ImportTemplateDialog
                open={importDialogOpen}
                onOpenChange={setImportDialogOpen}
                templates={templates}
                onImport={handleImportTemplate}
                title="Mindestbesetzungs-Template laden"
            />

            <AlertDialog open={importConfirmOpen} onOpenChange={setImportConfirmOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Template laden?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die aktuellen Mindestbesetzungs-Einstellungen werden durch die Template-Werte ersetzt.
                            Nicht gespeicherte Änderungen gehen dabei verloren.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel
                            onClick={() => {
                                setImportConfirmOpen(false);
                                setSelectedTemplateId(null);
                            }}
                        >
                            Abbrechen
                        </AlertDialogCancel>
                        <AlertDialogAction onClick={confirmImport}>Laden</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
