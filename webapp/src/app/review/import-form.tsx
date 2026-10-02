"use client";

import { useRef, useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { importFiles } from "./actions";

/** Upload an input.json/result.json pair; a rejected pair leaves the reviewed schedule unchanged. */
export function ImportForm() {
  const form = useRef<HTMLFormElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(files: FormData) {
    setError(null);
    startTransition(async () => {
      const result = await importFiles(files);
      if (result.ok) form.current?.reset();
      else setError(`${result.error} Der bisherige Dienstplan bleibt zur Prüfung.`);
    });
  }

  return (
    <Card className="max-w-3xl">
      <CardHeader>
        <CardTitle>Importieren</CardTitle>
        <CardDescription>
          Ein Paar aus input.json und result.json prüfen. Der Import veröffentlicht und speichert nichts.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form ref={form} action={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="import-input">input.json</Label>
              <Input id="import-input" name="input" type="file" accept=".json,application/json" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="import-result">result.json</Label>
              <Input id="import-result" name="result" type="file" accept=".json,application/json" required />
            </div>
          </div>
          <Button type="submit" disabled={pending}>
            {pending ? "Dateien werden geprüft …" : "Importieren"}
          </Button>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
