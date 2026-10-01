'use client';

import {Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,} from '@/components/ui/dialog';
import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {WishesAndBlockedForm} from './wishes-and-blocked-form';
import {ScrollArea} from '@/components/ui/scroll-area';

interface WishesAndBlockedDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    employee?: WishesAndBlockedEmployee;
    onSubmit: (data: WishesAndBlockedEmployee) => void;
    isSubmitting?: boolean;
    excludedEmployeeKeys?: number[];
    isGlobal?: boolean;
    caseId?: number;
    monthYear?: string;
}

export function WishesAndBlockedDialog({
                                           open,
                                           onOpenChange,
                                           employee,
                                           onSubmit,
                                           isSubmitting,
                                           isGlobal,
                                           excludedEmployeeKeys = [],
                                           caseId,
                                           monthYear,
                                       }: WishesAndBlockedDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[95vw] w-full sm:max-w-[50vw] max-h-[90vh]">
                <DialogHeader>
                    <DialogTitle>
                        {employee ? 'Mitarbeiter bearbeiten' : 'Neuer Eintrag'}
                    </DialogTitle>
                    <DialogDescription>
                        {employee
                            ? 'Bearbeite Wünsche und Blockierungen für diesen Mitarbeiter.'
                            : 'Füge einen neuen Mitarbeiter mit seinen Wünschen und Blockierungen hinzu.'}
                    </DialogDescription>
                </DialogHeader>
                <ScrollArea className="max-h-[calc(90vh-8rem)]">
                    <div className="pr-4">
                        <WishesAndBlockedForm
                            employee={employee}
                            onSubmit={onSubmit}
                            onCancel={() => onOpenChange(false)}
                            isSubmitting={isSubmitting}
                            excludedEmployeeKeys={excludedEmployeeKeys}
                            isGlobal={isGlobal}
                            caseId={caseId}
                            monthYear={monthYear}
                        />
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    );
}
