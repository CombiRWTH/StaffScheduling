"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PublicationResult } from "@/lib/types";
import type { WriteResult } from "@/lib/write-result";
import { clearSchedule, publishSchedule } from "./actions";

/**
 * A TimeOffice write that runs only after its exact effect was confirmed. It reports success only with the
 * backend's committed result; cancelling changes nothing.
 */
function ConfirmedAction({
  label,
  confirmation,
  confirmLabel,
  run,
  success,
  variant,
}: {
  label: string;
  confirmation: string;
  confirmLabel: string;
  run: () => Promise<WriteResult<PublicationResult>>;
  success: (result: PublicationResult) => string;
  variant?: "destructive";
}) {
  const [confirming, setConfirming] = useState(false);
  const [outcome, setOutcome] = useState<{ ok: boolean; message: string } | null>(null);
  const [pending, startTransition] = useTransition();

  function confirm() {
    startTransition(async () => {
      const result = await run();
      setConfirming(false);
      setOutcome(result.ok ? { ok: true, message: success(result.value) } : { ok: false, message: result.error });
    });
  }

  return (
    <div role="group" aria-label={label} className="space-y-3">
      {confirming ? (
        <div role="group" aria-label={`${label} bestätigen`} className="space-y-3 rounded-lg border bg-muted/30 p-4">
          <p>{confirmation}</p>
          <div className="flex flex-wrap gap-2">
            <Button variant={variant} disabled={pending} onClick={confirm}>
              {pending ? "TimeOffice wird geändert …" : confirmLabel}
            </Button>
            <Button variant="outline" disabled={pending} onClick={() => setConfirming(false)}>
              Abbrechen
            </Button>
          </div>
        </div>
      ) : (
        <Button
          variant={variant === "destructive" ? "outline" : undefined}
          onClick={() => {
            setOutcome(null);
            setConfirming(true);
          }}
        >
          {label}
        </Button>
      )}
      {outcome && (
        <p role={outcome.ok ? "status" : "alert"} className={outcome.ok ? undefined : "text-destructive"}>
          {outcome.message}
        </p>
      )}
    </div>
  );
}

/**
 * Publish the reviewed schedule to its stations' TimeOffice planning targets, or clear the selected stations'
 * published duties. `review` is the schedule under review when it belongs to the selection.
 */
export function PublicationCard({
  month,
  monthName,
  stations,
  review,
}: {
  month: string;
  monthName: string;
  stations: { id: number; name: string }[];
  review: { receivedAt: string; duties: number; accepted: boolean } | null;
}) {
  const ids = stations.map((station) => station.id);
  const scope = `${stations.map((station) => station.name).join(", ")} im ${monthName}`;
  const kept = "Abwesenheiten, Wünsche und andere Pläne bleiben unverändert.";

  return (
    <Card aria-label="Veröffentlichung" className="max-w-3xl">
      <CardHeader>
        <CardTitle>Veröffentlichen</CardTitle>
        <CardDescription>
          Schreibt Dienste in die Planungsziele von {scope} in TimeOffice. Generieren und Importieren veröffentlichen
          nie.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 text-sm">
        {!review ? (
          <p className="text-muted-foreground">Zum Veröffentlichen den Dienstplan dieser Auswahl prüfen.</p>
        ) : review.duties === 0 ? (
          <p className="text-muted-foreground">
            Ein Dienstplan ohne Dienste wird nicht veröffentlicht; veröffentlichte Dienste entfernt die Wartung.
          </p>
        ) : review.accepted ? (
          <ConfirmedAction
            label="In TimeOffice veröffentlichen"
            confirmLabel="Veröffentlichen bestätigen"
            confirmation={`Die veröffentlichten Dienste von ${scope} werden durch die ${review.duties} Dienste dieses Dienstplans ersetzt. ${kept}`}
            run={() => publishSchedule(month, ids, review.receivedAt)}
            success={(result) =>
              `Veröffentlicht: ${result.published_duties} Dienste geschrieben und gelesen, ${result.removed_duties} bisherige ersetzt.`
            }
          />
        ) : (
          <p className="text-muted-foreground">Nur ein angenommener Dienstplan kann veröffentlicht werden.</p>
        )}
        <div className="space-y-2 border-t pt-4">
          <p className="text-muted-foreground">Wartung: veröffentlichte Dienste dieser Auswahl entfernen.</p>
          <ConfirmedAction
            label="Veröffentlichte Dienste entfernen"
            confirmLabel="Entfernen bestätigen"
            confirmation={`Alle veröffentlichten Dienste von ${scope} werden aus TimeOffice entfernt. ${kept}`}
            run={() => clearSchedule(month, ids)}
            success={(result) => `Entfernt: ${result.removed_duties} veröffentlichte Dienste.`}
            variant="destructive"
          />
        </div>
      </CardContent>
    </Card>
  );
}
