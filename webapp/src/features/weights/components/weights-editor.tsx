'use client';

import {useEffect, useMemo, useState} from 'react';
import {WEIGHT_METADATA, Weights} from '@/entities/models/weights.model';
import {Label} from '@/components/ui/label';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {
    Info,
    // Save,
    // Upload,
} from 'lucide-react';
import {Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,} from '@/components/ui/tooltip';
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
    createWeightsTemplateAction,
    getWeightsTemplateAction,
    listWeightsTemplatesAction,
} from '@/features/templates/weights-templates.actions';
import {TemplateSummary} from '@/entities/models/template.model';
import {useSearchParams} from 'next/navigation';
import {toast} from 'sonner';

interface WeightsEditorProps {
    weights: Weights;
    onSave: (weights: Weights) => void;
    isSaving?: boolean;
    caseId?: number;
}

/**
 * Component for editing solver weight configurations.
 * Provides numeric inputs (no fixed min/max) for all weight values.
 */
export function WeightsEditor({weights, onSave, isSaving, caseId: caseIdProp}: WeightsEditorProps) {
    const searchParams = useSearchParams();
    const caseId = caseIdProp ?? parseInt(searchParams.get('caseId') ?? '0', 10);
    const [editedWeights, setEditedWeights] = useState<Weights>(weights);
    const [saveDialogOpen, setSaveDialogOpen] = useState(false);
    const [importDialogOpen, setImportDialogOpen] = useState(false);
    const [importConfirmOpen, setImportConfirmOpen] = useState(false);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
    const [templates, setTemplates] = useState<TemplateSummary[]>([]);
    const [isCreating, setIsCreating] = useState(false);

    // Fetch templates on mount
    useEffect(() => {
        if (!caseId) return;
        listWeightsTemplatesAction(caseId)
            .then(setTemplates)
            .catch(() => setTemplates([]));
    }, [caseId]);

    // Update local state when props change (deferred to avoid synchronous setState in effect)
    useEffect(() => {
        if (JSON.stringify(weights) !== JSON.stringify(editedWeights)) {
            Promise.resolve().then(() => setEditedWeights(weights));
        }
    }, [weights]);
    // Derived flag: are there unsaved changes?
    const hasChanges = useMemo(() => JSON.stringify(weights) !== JSON.stringify(editedWeights), [weights, editedWeights]);

    const handleWeightChange = (key: keyof Weights, value: number) => {
        // No enforced min/max for weights — accept the provided numeric value as-is
        setEditedWeights(prev => ({
            ...prev,
            [key]: value,
        }));
    };

    const handleSave = () => {
        onSave(editedWeights);
    };

    const handleReset = () => {
        setEditedWeights(weights);
    };

    const handleSaveAsTemplate = async (description: string) => {
        setIsCreating(true);
        const result = await createWeightsTemplateAction(caseId, editedWeights, description);
        if (!result.success) {
            toast.error(result.error);
            setIsCreating(false);
            return;
        }
        setSaveDialogOpen(false);
        // Refresh template list
        const updated = await listWeightsTemplatesAction(caseId);
        setTemplates(updated);
        toast.success('Template gespeichert');
        setIsCreating(false);
    };

    const handleImportTemplate = (templateId: string) => {
        setSelectedTemplateId(templateId);
        setImportDialogOpen(false);
        // Open confirmation dialog but do NOT perform import yet
        setImportConfirmOpen(true);
    };

    const confirmImport = async () => {
        if (!selectedTemplateId) return;
        try {
            const result = await getWeightsTemplateAction(caseId, selectedTemplateId);
            if (!result.success) {
                toast.error(result.error);
                return;
            }
            setEditedWeights(result.data.content);
        } finally {
            setImportConfirmOpen(false);
            setSelectedTemplateId(null);
        }
    };

    return (
        <div className="space-y-3">
            {WEIGHT_METADATA.map((metadata) => {
                const value = editedWeights[metadata.key];

                return (
                    <div key={metadata.key} className="border rounded-lg p-4 hover:bg-accent/5 transition-colors">
                        <div className="flex items-center justify-between gap-4 mb-2">
                            <div className="flex items-center gap-2 flex-1">
                                <Label className="font-medium text-sm">{metadata.label}</Label>
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help"/>
                                        </TooltipTrigger>
                                        <TooltipContent side="top" className="max-w-xs">
                                            <p className="text-xs">{metadata.description}</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <div className="w-28 sm:w-24 md:w-28">
                                <Input
                                    type="number"
                                    inputMode="numeric"
                                    value={value}
                                    onChange={(e) => handleWeightChange(metadata.key, parseInt(e.target.value) || 0)}
                                    className="w-full text-center h-8 text-sm"
                                />
                            </div>
                        </div>

                    </div>
                );
            })}

            <div className="flex gap-2 justify-between pt-4 border-t sticky bottom-0 bg-background py-3">
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
                        <Save className="mr-2 h-4 w-4"/>
                        Als Template speichern
                    </Button>
                </div>
                */}
                <div/>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={handleReset}
                        disabled={!hasChanges || isSaving}
                        size="sm"
                    >
                        Zurücksetzen
                    </Button>
                    <Button
                        onClick={handleSave}
                        disabled={!hasChanges || isSaving}
                        size="sm"
                    >
                        {isSaving ? 'Speichern...' : 'Speichern'}
                    </Button>
                </div>
            </div>

            <SaveTemplateDialog
                open={saveDialogOpen}
                onOpenChange={setSaveDialogOpen}
                onSave={handleSaveAsTemplate}
                isSaving={isCreating}
                title="Gewichtungen als Template speichern"
                descriptionPlaceholder="z.B. 'Standardkonfiguration für Nachtschichten' oder 'Optimiert für Wochenenden'"
            />

            <ImportTemplateDialog
                open={importDialogOpen}
                onOpenChange={setImportDialogOpen}
                templates={templates}
                onImport={handleImportTemplate}
                title="Gewichtungs-Template laden"
            />

            <AlertDialog open={importConfirmOpen} onOpenChange={setImportConfirmOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Template laden?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Die aktuellen Gewichtungen werden durch das gewählte Template ersetzt.
                            Nicht gespeicherte Änderungen gehen verloren. Möchten Sie fortfahren?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => setSelectedTemplateId(null)}>
                            Abbrechen
                        </AlertDialogCancel>
                        <AlertDialogAction onClick={confirmImport}>
                            Laden
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
