"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MinimalStaffEditor } from "@/features/minimal-staff/components/minimal-staff-editor";
import { updateMinimalStaffAction } from "@/features/minimal-staff/minimal-staff.actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, UserCog } from "lucide-react";
import { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

interface MinimalStaffCaseData {
  caseId: number;
  requirements: MinimalStaffRequirements;
}

interface MinimalStaffCaseError {
  caseId: number;
  error: string;
}

interface MinimalStaffPageClientProps {
  monthYear: string;
  minimalStaffCases: MinimalStaffCaseData[];
  minimalStaffErrors: MinimalStaffCaseError[];
  availableCaseIds: number[];
}

function MinimalStaffCaseCard({ caseId, monthYear, requirements }: MinimalStaffCaseData & { monthYear: string }) {
  const [isPending, startTransition] = useTransition();

  const handleSave = (newRequirements: MinimalStaffRequirements) => {
    startTransition(async () => {
      const result = await updateMinimalStaffAction(caseId, monthYear, newRequirements);
      if (!result.success) {
        toast.error(result.error);
        return;
      }
      toast.success("Mindestbesetzung erfolgreich aktualisiert");
    });
  };

  return (
    <div className="py-6 space-y-4">
      {/* Info Banner */}
      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertTitle>Personalplanung optimieren</AlertTitle>
        <AlertDescription>
          Legen Sie hier fest, wie viele Mitarbeiter jeder Kategorie mindestens pro Schicht eingeplant werden müssen.
          Diese Vorgaben werden bei der automatischen Dienstplanerstellung berücksichtigt.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <UserCog className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle>Mindestbesetzung konfigurieren</CardTitle>
              <CardDescription>
                Case {caseId}: Verwalten Sie die Mindestanforderungen für alle Mitarbeiterkategorien
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <MinimalStaffEditor requirements={requirements} onSave={handleSave} isSaving={isPending} caseId={caseId} />
        </CardContent>
      </Card>
    </div>
  );
}

export function MinimalStaffPageClient({
  monthYear,
  minimalStaffCases,
  minimalStaffErrors,
  availableCaseIds,
}: MinimalStaffPageClientProps) {
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
  const visibleErrors = minimalStaffErrors.filter(({ caseId }) => visibleCaseIds.includes(caseId));

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
          <CardTitle>Mindestbesetzung konfigurieren</CardTitle>
          <CardDescription>Wähle, welche Cases angezeigt werden sollen.</CardDescription>
          <div className="flex flex-wrap gap-2 pt-2">
            {sortedAvailableCaseIds.map((caseId) => (
              <Button
                key={caseId}
                type="button"
                size="sm"
                variant={visibleCaseIds.includes(caseId) ? "default" : "outline"}
                onClick={() => toggleCase(caseId)}
              >
                Case {caseId}
              </Button>
            ))}
          </div>
        </CardHeader>
      </Card>

      {visibleErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Mindestbesetzung konnte nicht geladen werden</AlertTitle>
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
      ) : minimalStaffCases.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Keine Mindestbesetzung gefunden.</div>
      ) : (
        minimalStaffCases.map(({ caseId, requirements }) => (
          <MinimalStaffCaseCard key={caseId} caseId={caseId} monthYear={monthYear} requirements={requirements} />
        ))
      )}
    </div>
  );
}
