"use client";

import {useState} from "react";
import {Button} from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {Label} from "@/components/ui/label";
import {Textarea} from "@/components/ui/textarea";

interface DescriptionInputDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: (description?: string) => void;
    isLoading?: boolean;
}

export function DescriptionInputDialog({
                                           open,
                                           onOpenChange,
                                           onConfirm,
                                           isLoading = false,
                                       }: DescriptionInputDialogProps) {
    const [description, setDescription] = useState<string>("");

    const handleConfirm = () => {
        onConfirm(description.trim() || undefined);
        setDescription(""); // Reset for next time
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Beschreibung hinzufügen (optional)</DialogTitle>
                    <DialogDescription>
                        Sie können eine optionale Beschreibung für diesen Dienstplan hinzufügen.
                        Dies hilft bei der Identifizierung und Organisation Ihrer Dienstpläne.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="description">Beschreibung</Label>
                        <Textarea
                            id="description"
                            placeholder="z.B. Weihnachtsschicht, Sommerferiendienst..."
                            value={description}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
                            disabled={isLoading}
                            autoFocus
                            rows={3}
                            maxLength={500}
                        />
                        <p className="text-sm text-muted-foreground">
                            Lassen Sie das Feld leer, wenn Sie keine Beschreibung hinzufügen möchten.
                        </p>
                    </div>
                </div>
                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={isLoading}
                    >
                        Abbrechen
                    </Button>
                    <Button onClick={handleConfirm} disabled={isLoading}>
                        {isLoading ? "Speichert..." : "Bestätigen"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
