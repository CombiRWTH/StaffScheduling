"use client";

import { useState, useTransition } from "react";
import { ChevronDown, Download, Upload } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { PublicationResult } from "@/lib/types";
import type { WriteResult } from "@/lib/write-result";
import { cn } from "@/lib/utils";
import { clearSchedule, importFiles, publishSchedule } from "./actions";

type Outcome = { ok: boolean; message: string } | null;

/**
 * A TimeOffice write behind a confirmation popover that names its exact effect. Success is reported only
 * with the backend's committed result; cancelling changes nothing.
 */
function ConfirmedAction({
  label,
  confirmation,
  confirmLabel,
  run,
  success,
  onOutcome,
  primary,
}: {
  label: string;
  confirmation: string;
  confirmLabel: string;
  run: () => Promise<WriteResult<PublicationResult>>;
  success: (result: PublicationResult) => string;
  onOutcome: (outcome: Outcome) => void;
  primary?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();

  function confirm() {
    startTransition(async () => {
      const result = await run();
      setOpen(false);
      onOutcome(result.ok ? { ok: true, message: success(result.value) } : { ok: false, message: result.error });
    });
  }

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        if (pending) return;
        if (next) onOutcome(null);
        setOpen(next);
      }}
    >
      <PopoverTrigger asChild>
        <Button variant={primary ? "default" : "outline"}>{label}</Button>
      </PopoverTrigger>
      <PopoverContent role="dialog" aria-label={label} align="start" className="w-96 space-y-3 text-sm">
        <p>{confirmation}</p>
        <div className="flex flex-wrap gap-2">
          <Button variant={primary ? "default" : "destructive"} disabled={pending} onClick={confirm}>
            {pending ? "TimeOffice wird geändert …" : confirmLabel}
          </Button>
          <Button variant="outline" disabled={pending} onClick={() => setOpen(false)}>
            Abbrechen
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

/** The schedule's four portable files, readable and checkable without TimeOffice; a diagnosis unless accepted. */
function DownloadMenu({ files, accepted }: { files: readonly string[]; accepted: boolean }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">
          <Download />
          Herunterladen
          <ChevronDown />
        </Button>
      </PopoverTrigger>
      <PopoverContent role="dialog" aria-label="Herunterladen" align="start" className="w-64 p-1">
        {files.map((name) => (
          <a
            key={name}
            href={`/review/files/${name}`}
            download
            className={cn(buttonVariants({ variant: "ghost" }), "w-full justify-start")}
          >
            {name}
          </a>
        ))}
        <p className="px-3 py-2 text-xs text-muted-foreground">
          {accepted
            ? "Ohne TimeOffice lesbar und prüfbar."
            : "Nicht angenommen: Die Dateien sind eine Diagnose, kein verwendbarer Dienstplan."}
        </p>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Upload an input.json/result.json pair; a rejected pair leaves the reviewed schedule unchanged and keeps the
 * chosen files for another try. Closing the popover discards the form.
 */
function ImportMenu({ onOpen }: { onOpen: () => void }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  // A submit handler instead of a form action: React resets a form after its action, also a failed one.
  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const files = new FormData(event.currentTarget);
    setError(null);
    startTransition(async () => {
      const result = await importFiles(files);
      if (result.ok) setOpen(false);
      else setError(`${result.error} Der bisherige Dienstplan bleibt zur Prüfung.`);
    });
  }

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        if (pending) return;
        if (next) {
          setError(null);
          onOpen();
        }
        setOpen(next);
      }}
    >
      <PopoverTrigger asChild>
        <Button variant="outline">
          <Upload />
          Importieren
        </Button>
      </PopoverTrigger>
      <PopoverContent role="dialog" aria-label="Importieren" align="start" className="w-96 text-sm">
        <form onSubmit={submit} className="space-y-3">
          <p className="text-muted-foreground">
            Ein Paar aus input.json und result.json prüfen. Der Import ersetzt den Dienstplan zur Prüfung und
            veröffentlicht nichts.
          </p>
          <div className="space-y-2">
            <Label htmlFor="import-input">input.json</Label>
            <Input id="import-input" name="input" type="file" accept=".json,application/json" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="import-result">result.json</Label>
            <Input id="import-result" name="result" type="file" accept=".json,application/json" required />
          </div>
          <Button type="submit" disabled={pending}>
            {pending ? "Dateien werden geprüft …" : "Dateien importieren"}
          </Button>
          {error && (
            <p role="alert" className="text-destructive">
              {error}
            </p>
          )}
        </form>
      </PopoverContent>
    </Popover>
  );
}

/**
 * What a staff admin does with the schedule: publish it to the selected stations' TimeOffice plans, download
 * or import files, and remove published duties. `review` is the schedule under review when it belongs to
 * the selection; without it, only import and removal are offered.
 */
export function ReviewActions({
  month,
  monthName,
  stations,
  review,
  files,
}: {
  month: string;
  monthName: string;
  stations: { id: number; name: string }[];
  review: { receivedAt: string; duties: number; accepted: boolean } | null;
  files: readonly string[];
}) {
  const [outcome, setOutcome] = useState<Outcome>(null);
  const ids = stations.map((station) => station.id);
  const scope = `${stations.map((station) => station.name).join(", ")} im ${monthName}`;
  const kept = "Abwesenheiten, Wünsche und andere Pläne bleiben unverändert.";
  const publishable = review !== null && review.accepted && review.duties > 0;

  return (
    <div role="group" aria-label="Veröffentlichung" className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {publishable && (
          <ConfirmedAction
            primary
            label="In TimeOffice veröffentlichen"
            confirmLabel="Veröffentlichen bestätigen"
            confirmation={`Die veröffentlichten Dienste von ${scope} werden durch die ${review.duties} Dienste dieses Dienstplans ersetzt. ${kept}`}
            run={() => publishSchedule(month, ids, review.receivedAt)}
            success={(result) =>
              `Veröffentlicht: ${result.published_duties} Dienste geschrieben und gelesen, ${result.removed_duties} bisherige ersetzt.`
            }
            onOutcome={setOutcome}
          />
        )}
        {review && <DownloadMenu files={files} accepted={review.accepted} />}
        <ImportMenu onOpen={() => setOutcome(null)} />
        {ids.length > 0 && (
          <ConfirmedAction
            label="Veröffentlichte Dienste entfernen"
            confirmLabel="Entfernen bestätigen"
            confirmation={`Alle veröffentlichten Dienste von ${scope} werden aus TimeOffice entfernt. ${kept}`}
            run={() => clearSchedule(month, ids)}
            success={(result) => `Entfernt: ${result.removed_duties} veröffentlichte Dienste.`}
            onOutcome={setOutcome}
          />
        )}
      </div>
      {review && !publishable && (
        <p className="text-sm text-muted-foreground">
          {review.duties === 0
            ? "Ein Dienstplan ohne Dienste wird nicht veröffentlicht."
            : "Nur ein angenommener Dienstplan kann veröffentlicht werden."}
        </p>
      )}
      {outcome && (
        <p role={outcome.ok ? "status" : "alert"} className={cn("text-sm", !outcome.ok && "text-destructive")}>
          {outcome.message}
        </p>
      )}
    </div>
  );
}
