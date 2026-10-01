'use client';

import {useEffect, useState} from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {Label} from '@/components/ui/label';
import {Textarea} from '@/components/ui/textarea';
import {Loader2} from 'lucide-react';

interface EditTemplateDescriptionDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    currentDescription: string;
    onSave: (newDescription: string) => void;
    isSaving?: boolean;
}

/**
 * Dialog for editing a template's description.
 */
export function EditTemplateDescriptionDialog({
                                                  open,
                                                  onOpenChange,
                                                  currentDescription,
                                                  onSave,
                                                  isSaving = false,
                                              }: EditTemplateDescriptionDialogProps) {
    const [description, setDescription] = useState(currentDescription);

    // Update local state when currentDescription changes
    useEffect(() => {
        setDescription(currentDescription);
    }, [currentDescription]);

    const handleSave = () => {
        if (description.trim()) {
            onSave(description);
        }
    };

    const handleCancel = () => {
        setDescription(currentDescription);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Beschreibung bearbeiten</DialogTitle>
                    <DialogDescription>
                        Ändern Sie die Beschreibung des Templates.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                    <Label htmlFor="description">Beschreibung</Label>
                    <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Geben Sie eine Beschreibung ein..."
                        rows={4}
                        disabled={isSaving}
                    />
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                        Abbrechen
                    </Button>
                    <Button
                        onClick={handleSave}
                        disabled={!description.trim() || isSaving}
                    >
                        {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                        Speichern
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
