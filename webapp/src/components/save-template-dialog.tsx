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
import {Label} from '@/components/ui/label';
import {Textarea} from '@/components/ui/textarea';
import {Loader2} from 'lucide-react';

interface SaveTemplateDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSave: (description: string) => void;
    isSaving?: boolean;
    title?: string;
    descriptionPlaceholder?: string;
}

/**
 * Dialog for saving content as a template with a description.
 */
export function SaveTemplateDialog({
                                       open,
                                       onOpenChange,
                                       onSave,
                                       isSaving = false,
                                       title = 'Als Template speichern',
                                       descriptionPlaceholder = 'Geben Sie eine Beschreibung für das Template ein...',
                                   }: SaveTemplateDialogProps) {
    const [description, setDescription] = useState('');

    const handleSave = () => {
        if (description.trim()) {
            onSave(description);
            setDescription('');
        }
    };

    const handleCancel = () => {
        setDescription('');
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    <DialogDescription>
                        Geben Sie eine aussagekräftige Beschreibung ein, um das Template später leicht wiederzufinden.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                    <Label htmlFor="description">Beschreibung</Label>
                    <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder={descriptionPlaceholder}
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
