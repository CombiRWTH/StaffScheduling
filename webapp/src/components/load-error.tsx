import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

/** A failed read with what the user can do next. */
export function LoadError({ title, message }: { title: string; message: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        <p>Auswahl prüfen oder Stationen aktualisieren.</p>
      </AlertDescription>
    </Alert>
  );
}
