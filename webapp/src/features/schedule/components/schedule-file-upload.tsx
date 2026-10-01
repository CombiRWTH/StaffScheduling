"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { ScheduleSolutionRaw } from "@/entities/models/schedule.model";

interface ScheduleFileUploadProps {
  onFileLoaded: (data: ScheduleSolutionRaw) => void;
  isLoading?: boolean;
}

/**
 * Component for uploading schedule solution JSON files.
 * Validates and parses the file before calling the onFileLoaded callback.
 */
export function ScheduleFileUpload({ onFileLoaded, isLoading }: ScheduleFileUploadProps) {
  const [fileName, setFileName] = useState<string>("");
  const [error, setError] = useState<string>("");

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    console.log("file", file);
    if (!file) return;

    setError("");
    setFileName(file.name);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target?.result as string);

        // Basic validation
        if (!jsonData.variables || !jsonData.employees || !jsonData.shifts || !jsonData.days) {
          throw new Error("Invalid solution file format");
        }

        onFileLoaded(jsonData);
      } catch (err) {
        setError("Failed to parse solution file. Please check the file format.");
        console.error(err);
      } finally {
        // Reset the input value to allow uploading the same file again
        event.target.value = "";
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="flex">
      <div className="flex gap-2">
        <Button
          onClick={() => document.getElementById("file-upload")?.click()}
          variant="outline"
          className="gap-2 w-full justify-start"
          disabled={isLoading}
        >
          <Plus className="h-4 w-4" />
        </Button>
        <input
          id="file-upload"
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          className="hidden"
          disabled={isLoading}
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
