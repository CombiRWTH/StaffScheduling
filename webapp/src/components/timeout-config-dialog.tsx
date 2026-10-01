'use client';

import {useState} from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {RadioGroup, RadioGroupItem} from '@/components/ui/radio-group';
import {Clock, Loader2} from 'lucide-react';

interface TimeoutConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: (timeout: number) => void;
    isExecuting: boolean;
    actionTitle: string;
}

const PRESET_TIMEOUTS = [
    {value: 30, label: '30 Sekunden'},
    {value: 45, label: '45 Sekunden'},
    {value: 60, label: '1 Minute'},
    {value: 120, label: '2 Minuten'},
    {value: 300, label: '5 Minuten'},
];

export function TimeoutConfigDialog({
                                        open,
                                        onOpenChange,
                                        onConfirm,
                                        isExecuting,
                                        actionTitle,
                                    }: TimeoutConfigDialogProps) {
    const [timeoutMode, setTimeoutMode] = useState<'preset' | 'custom'>('preset');
    const [selectedPreset, setSelectedPreset] = useState<number>(60);
    const [customTimeout, setCustomTimeout] = useState<string>('60');
    const [error, setError] = useState<string>('');

    const handleConfirm = () => {
        setError('');

        const timeout = timeoutMode === 'preset' ? selectedPreset : parseInt(customTimeout);

        if (isNaN(timeout) || timeout <= 0) {
            setError('Bitte geben Sie eine gültige Zahl größer als 0 ein');
            return;
        }

        if (timeout > 3600) {
            setError('Timeout darf maximal 3600 Sekunden (1 Stunde) betragen');
            return;
        }

        onConfirm(timeout);
    };

    const handleCancel = () => {
        setError('');
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5"/>
                        Timeout konfigurieren
                    </DialogTitle>
                    <DialogDescription>
                        Legen Sie fest, wie lange {actionTitle} maximal laufen soll, bevor der Vorgang abgebrochen wird.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 py-4">
                    <div className="space-y-4">
                        <Label>Timeout-Option wählen</Label>

                        {/* Preset Options */}
                        <div className="space-y-3">
                            <div className="flex items-center space-x-2">
                                <input
                                    type="radio"
                                    id="preset"
                                    checked={timeoutMode === 'preset'}
                                    onChange={() => setTimeoutMode('preset')}
                                    className="h-4 w-4"
                                />
                                <Label htmlFor="preset" className="font-normal cursor-pointer">
                                    Vordefinierte Optionen
                                </Label>
                            </div>

                            {timeoutMode === 'preset' && (
                                <RadioGroup
                                    value={selectedPreset.toString()}
                                    onValueChange={(value) => setSelectedPreset(parseInt(value))}
                                    className="ml-6 space-y-2"
                                >
                                    {PRESET_TIMEOUTS.map((preset) => (
                                        <div key={preset.value} className="flex items-center space-x-2">
                                            <RadioGroupItem value={preset.value.toString()}
                                                            id={`preset-${preset.value}`}/>
                                            <Label htmlFor={`preset-${preset.value}`}
                                                   className="font-normal cursor-pointer">
                                                {preset.label}
                                            </Label>
                                        </div>
                                    ))}
                                </RadioGroup>
                            )}
                        </div>

                        {/* Custom Input */}
                        <div className="space-y-3">
                            <div className="flex items-center space-x-2">
                                <input
                                    type="radio"
                                    id="custom"
                                    checked={timeoutMode === 'custom'}
                                    onChange={() => setTimeoutMode('custom')}
                                    className="h-4 w-4"
                                />
                                <Label htmlFor="custom" className="font-normal cursor-pointer">
                                    Individuelle Eingabe
                                </Label>
                            </div>

                            {timeoutMode === 'custom' && (
                                <div className="ml-6 space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Input
                                            type="number"
                                            min="1"
                                            max="3600"
                                            value={customTimeout}
                                            onChange={(e) => setCustomTimeout(e.target.value)}
                                            placeholder="z.B. 180"
                                            className="max-w-[200px]"
                                        />
                                        <span className="text-sm text-muted-foreground">Sekunden</span>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Wert zwischen 1 und 3600 Sekunden
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {error && (
                        <p className="text-sm text-red-600">{error}</p>
                    )}
                </div>

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={isExecuting}
                    >
                        Abbrechen
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        disabled={isExecuting}
                    >
                        {isExecuting && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                        {isExecuting ? 'Wird ausgeführt...' : 'Starten'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
