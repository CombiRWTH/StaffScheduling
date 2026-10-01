"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WeightsEditor } from "@/features/weights/components/weights-editor";
import { updateWeightsAction } from "@/features/weights/weights.actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Info, Scale } from "lucide-react";
import { Weights } from "@/entities/models/weights.model";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

interface WeightsCaseData {
  caseId: number;
  weights: Weights;
}

interface WeightsCaseError {
  caseId: number;
  error: string;
}

interface WeightsPageClientProps {
  monthYear: string;
  weightsCases: WeightsCaseData[];
  weightsErrors: WeightsCaseError[];
  availableCaseIds: number[];
}

function WeightsCaseCard({ caseId, monthYear, weights }: WeightsCaseData & { monthYear: string }) {
  const [isPending, startTransition] = useTransition();

  const handleSave = (newWeights: Weights) => {
    startTransition(async () => {
      const result = await updateWeightsAction(caseId, monthYear, newWeights);
      if (!result.success) {
        toast.error(result.error);
        return;
      }
      toast.success("Gewichtungen erfolgreich aktualisiert");
    });
  };

  return (
    <div className="py-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Scale className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <CardTitle>Solver-Gewichtungen</CardTitle>
              <CardDescription>
                Case {caseId}: Konfigurieren Sie die Wichtigkeit der verschiedenen Optimierungsziele für den
                Scheduling-Solver
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Hinweis</AlertTitle>
        <AlertDescription>
          Höhere Werte bedeuten, dass das entsprechende Ziel stärker gewichtet wird. Ein Wert von 0 deaktiviert das Ziel
          komplett. Änderungen werden sofort für neue Solver-Läufe verwendet.
        </AlertDescription>
      </Alert>

      <WeightsEditor weights={weights} onSave={handleSave} isSaving={isPending} caseId={caseId} />
    </div>
  );
}

export function WeightsPageClient({
  monthYear,
  weightsCases,
  weightsErrors,
  availableCaseIds,
}: WeightsPageClientProps) {
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
  const visibleErrors = weightsErrors.filter(({ caseId }) => visibleCaseIds.includes(caseId));

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
          <CardTitle>Solver-Gewichtungen</CardTitle>
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
          <AlertTitle>Gewichtungen konnten nicht geladen werden</AlertTitle>
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
      ) : weightsCases.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Keine Gewichtungen gefunden.</div>
      ) : (
        weightsCases.map(({ caseId, weights }) => (
          <WeightsCaseCard key={caseId} caseId={caseId} monthYear={monthYear} weights={weights} />
        ))
      )}
    </div>
  );
}
