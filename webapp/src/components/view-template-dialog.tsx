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
import {Label} from '@/components/ui/label';
import {WEIGHT_METADATA, Weights} from '@/entities/models/weights.model';
import {Badge} from '@/components/ui/badge';
import {ScrollArea} from '@/components/ui/scroll-area';

interface ViewTemplateDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    template: {
        description: string;
        content: Weights;
        last_modified: string;
    } | null;
}

/**
 * Dialog for viewing template content without loading it.
 */
export function ViewTemplateDialog({
                                       open,
                                       onOpenChange,
                                       template,
                                   }: ViewTemplateDialogProps) {
    if (!template) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Template-Vorschau</DialogTitle>
                    <DialogDescription>{template.description}</DialogDescription>
                </DialogHeader>

                <ScrollArea className="max-h-[500px] pr-4">
                    <div className="space-y-3">
                        {WEIGHT_METADATA.map((metadata) => {
                            const value = template.content[metadata.key];

                            return (
                                <div
                                    key={metadata.key}
                                    className="border rounded-lg p-4 bg-muted/30"
                                >
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex-1">
                                            <Label className="font-medium text-sm">
                                                {metadata.label}
                                            </Label>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {metadata.description}
                                            </p>
                                        </div>
                                        <Badge variant="secondary" className="text-base px-4 py-1">
                                            {value}
                                        </Badge>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
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
