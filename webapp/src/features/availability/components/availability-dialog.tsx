"use client";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { AvailabilityForm } from "./availability-form";

interface AvailabilityDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  employee?: AvailabilityEmployee;
  onSubmit: (data: AvailabilityEmployee) => void;
  isSubmitting?: boolean;
  excludedEmployeeKeys?: number[];
  isGlobal?: boolean;
  caseId?: number;
  monthYear?: string;
}

export function AvailabilityDialog({
  open,
  onOpenChange,
  employee,
  onSubmit,
  isSubmitting,
  excludedEmployeeKeys = [],
  isGlobal,
  caseId,
  monthYear,
}: AvailabilityDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] w-full sm:max-w-[50vw] max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>{employee ? "Availability bearbeiten" : "Neue Availability"}</DialogTitle>
          <DialogDescription>
            {isGlobal
              ? "Lege fest, an welchen Wochentagen der Mitarbeiter grundsätzlich verfügbar ist."
              : "Lege fest, an welchen Tagen der Mitarbeiter in diesem Monat verfügbar ist."}
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[calc(90vh-8rem)]">
          <div className="pr-4">
            <AvailabilityForm
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
