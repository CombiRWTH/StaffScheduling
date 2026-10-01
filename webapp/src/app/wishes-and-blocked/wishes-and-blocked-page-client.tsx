"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Plus } from "lucide-react";
import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { WishesAndBlockedList } from "@/features/wishes_and_blocked/components/wishes-and-blocked-list";
import { WishesAndBlockedDialog } from "@/features/wishes_and_blocked/components/wishes-and-blocked-dialog";
import { toast } from "sonner";

import {
  createWishesAction,
  deleteWishesAction,
  updateWishesAction,
} from "@/features/wishes_and_blocked/wishes-and-blocked.actions";

interface WishesCaseData {
  caseId: number;
  employees: WishesAndBlockedEmployee[];
}

interface WishesCaseError {
  caseId: number;
  error: string;
}

interface WishesAndBlockedPageClientProps {
  caseId: number;
  monthYear: string;
  employees: WishesAndBlockedEmployee[];
}

interface WishesAndBlockedMultiCasePageClientProps {
  monthYear: string;
  wishesCases: WishesCaseData[];
  wishesErrors: WishesCaseError[];
  availableCaseIds: number[];
}

function WishesAndBlockedCaseCard({ caseId, monthYear, employees }: WishesAndBlockedPageClientProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<WishesAndBlockedEmployee | undefined>();
  const [isSubmitting, startSubmitTransition] = useTransition();
  const [isDeleting, startDeleteTransition] = useTransition();

  // Get list of employee keys that already have wishes
  const existingEmployeeKeys = employees.map((emp) => emp.key);

  const handleCreate = () => {
    setEditingEmployee(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (employee: WishesAndBlockedEmployee) => {
    setEditingEmployee(employee);
    setDialogOpen(true);
  };

  const handleSubmit = async (data: WishesAndBlockedEmployee) => {
    startSubmitTransition(async () => {
      let result;
      if (editingEmployee) {
        result = await updateWishesAction(caseId, monthYear, editingEmployee.key, data);
      } else {
        result = await createWishesAction(caseId, monthYear, data);
      }
      if (!result.success) {
        toast.error(result.error);
        return;
      }
      setDialogOpen(false);
      setEditingEmployee(undefined);
    });
  };

  const handleDelete = async (id: number) => {
    if (confirm("Möchtest du diesen Eintrag wirklich löschen?")) {
      startDeleteTransition(async () => {
        const result = await deleteWishesAction(caseId, monthYear, id);
        if (!result.success) {
          toast.error(result.error);
        }
      });
    }
  };

  return (
    <div className="py-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Wünsche & Blockierungen diesen Monat</CardTitle>
              <CardDescription>
                Case {caseId}: Verwalte freie und blockierte Tage und Schichten für diesen Monat
              </CardDescription>
            </div>
            <Button onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              Neuer Eintrag
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <WishesAndBlockedList
            employees={employees}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
        </CardContent>
      </Card>

      <WishesAndBlockedDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        employee={editingEmployee}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        excludedEmployeeKeys={existingEmployeeKeys}
        caseId={caseId}
        monthYear={monthYear}
      />
    </div>
  );
}

export function WishesAndBlockedPageClient({
  monthYear,
  wishesCases,
  wishesErrors,
  availableCaseIds,
}: WishesAndBlockedMultiCasePageClientProps) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const visibleCaseIds = Array.from(
    new Set(
      (searchParams.get("caseIds") ?? searchParams.get("caseId") ?? "")
        .split(",")
        .map((id) => Number(id))
        .filter((id) => Number.isInteger(id) && id > 0),
    ),
  );

  const sortedAvailableCaseIds = [...availableCaseIds].sort((a, b) => a - b);
  const visibleErrors = wishesErrors.filter(({ caseId }) => visibleCaseIds.includes(caseId));

  const toggleCase = (caseId: number) => {
    const nextCaseIds = visibleCaseIds.includes(caseId)
      ? visibleCaseIds.filter((id) => id !== caseId)
      : [...visibleCaseIds, caseId];

    const params = new URLSearchParams(searchParams.toString());
    if (nextCaseIds.length > 0) {
      params.set("caseIds", nextCaseIds.join(","));
      params.set("caseId", String(nextCaseIds[0]));
    } else {
      params.delete("caseIds");
      params.delete("caseId");
    }

    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="py-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Wünsche & Blockierungen diesen Monat</CardTitle>
          <CardDescription>Wähle, welche Cases angezeigt werden sollen.</CardDescription>
          <div className="flex flex-wrap gap-2 pt-2">
            {sortedAvailableCaseIds.map((caseId) => {
              const active = visibleCaseIds.includes(caseId);
              return (
                <Button
                  key={caseId}
                  type="button"
                  size="sm"
                  variant={active ? "default" : "outline"}
                  onClick={() => toggleCase(caseId)}
                >
                  Case {caseId}
                </Button>
              );
            })}
          </div>
        </CardHeader>
      </Card>

      {visibleErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Wünsche konnten nicht geladen werden</AlertTitle>
          <AlertDescription>
            {visibleErrors.map(({ caseId, error }) => (
              <div key={caseId}>
                Case {caseId}: {error}
              </div>
            ))}
          </AlertDescription>
        </Alert>
      )}

      {visibleCaseIds.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Wähle mindestens einen Case aus.</div>
      ) : wishesCases.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Keine Wünsche gefunden.</div>
      ) : (
        wishesCases.map(({ caseId, employees }) => (
          <WishesAndBlockedCaseCard key={caseId} caseId={caseId} monthYear={monthYear} employees={employees} />
        ))
      )}
    </div>
  );
}
