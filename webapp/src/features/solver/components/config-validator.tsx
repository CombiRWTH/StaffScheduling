"use client";

import { useState, useTransition } from "react";
import { checkSolverHealth } from "@/features/solver/solver.actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import type { SolverHealthResult } from "@/application/ports/solver.service";

interface ConfigValidatorProps {
  initialData: SolverHealthResult | null;
}

export function ConfigValidator({ initialData }: ConfigValidatorProps) {
  const [data, setData] = useState(initialData);
  const [isError, setIsError] = useState(initialData === null);
  const [isFetching, startRefetchTransition] = useTransition();

  const refetch = () => {
    startRefetchTransition(async () => {
      const result = await checkSolverHealth();
      if (!result.success) {
        setIsError(true);
        return;
      }
      setData(result.data);
      setIsError(false);
    });
  };

  if (isError) {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Fehler</AlertTitle>
        <AlertDescription>Solver-API konnte nicht erreicht werden</AlertDescription>
      </Alert>
    );
  }

  if (!data) {
    return null;
  }

  // API not healthy
  if (!data.healthy) {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Solver nicht erreichbar</AlertTitle>
        <AlertDescription>
          <p>{data.message}</p>
          {data.details && <p className="text-sm text-muted-foreground mt-1">{data.details}</p>}
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? (
              <>
                <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                Teste...
              </>
            ) : (
              "Erneut testen"
            )}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  // API healthy
  return (
    <Alert className="border-green-200 bg-green-50">
      <CheckCircle2 className="h-4 w-4 text-green-600" />
      <AlertTitle className="text-green-900">Solver erreichbar</AlertTitle>
      <AlertDescription className="text-green-700">
        <p className="text-sm">{data.message}</p>
        {data.details && <p className="text-sm mt-1">{data.details}</p>}
        <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? (
            <>
              <Loader2 className="h-3 w-3 mr-2 animate-spin" />
              Teste...
            </>
          ) : (
            "Erneut testen"
          )}
        </Button>
      </AlertDescription>
    </Alert>
  );
}
