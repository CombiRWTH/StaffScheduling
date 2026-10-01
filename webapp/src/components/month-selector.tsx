"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FetchCaseDialog } from "@/features/cases/components/fetch-case-dialog";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, Plus, RefreshCw } from "lucide-react";
import { formatMonthYear, parseMonthYear } from "@/lib/utils/case-utils";
import { CaseUnit } from "@/entities/models/case.model";
import { listCasesAction, refreshCasesFromSolverOptionsAction } from "@/features/cases/cases.actions";

interface MonthSelectorProps {
  disabled?: boolean;
  lockedCaseId?: number | null;
  lockedMonthYear?: string | null;
}

export function MonthSelector({ disabled, lockedCaseId, lockedMonthYear }: MonthSelectorProps) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [availableCases, setAvailableCases] = useState<CaseUnit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingOptions, setIsRefreshingOptions] = useState(false);
  const [isCasesOpen, setIsCasesOpen] = useState(false);
  const [yearInput, setYearInput] = useState("");
  const lastAutoRefreshMonthYearRef = useRef<string | null>(null);

  const urlMonthYear = searchParams.get("monthYear");
  const urlCaseIds = searchParams.get("caseIds");

  const effectiveMonthYear = disabled && lockedMonthYear ? lockedMonthYear : (urlMonthYear ?? "");

  const selectedMonthYear = useMemo(() => {
    if (/^(0?[1-9]|1[0-2])_\d{4}$/.test(effectiveMonthYear)) {
      return parseMonthYear(effectiveMonthYear);
    }

    const today = new Date();
    return {
      month: today.getMonth() + 1,
      year: today.getFullYear(),
    };
  }, [effectiveMonthYear]);

  const selectedCaseIds = useMemo(() => {
    if (disabled && lockedCaseId != null) {
      return [lockedCaseId];
    }

    return urlCaseIds
      ? urlCaseIds
          .split(",")
          .map(Number)
          .filter((id) => !Number.isNaN(id))
      : [];
  }, [disabled, lockedCaseId, urlCaseIds]);

  const refreshCases = useCallback(
    async (monthYear = effectiveMonthYear, refreshPage = false) => {
      setIsLoading(true);

      try {
        const data = monthYear ? await refreshCasesFromSolverOptionsAction(monthYear) : await listCasesAction();
        setAvailableCases(data.units ?? []);
        if (refreshPage) {
          router.refresh();
        }
      } catch {
        try {
          const data = await listCasesAction();
          setAvailableCases(data.units ?? []);
        } catch {
          setAvailableCases([]);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [effectiveMonthYear, router],
  );

  useEffect(() => {
    const shouldRefreshPage = Boolean(
      effectiveMonthYear &&
      lastAutoRefreshMonthYearRef.current !== null &&
      lastAutoRefreshMonthYearRef.current !== effectiveMonthYear,
    );

    lastAutoRefreshMonthYearRef.current = effectiveMonthYear;
    refreshCases(effectiveMonthYear, shouldRefreshPage);
  }, [effectiveMonthYear, refreshCases]);

  useEffect(() => {
    setYearInput(String(selectedMonthYear.year));
  }, [selectedMonthYear.year]);

  const refreshCasesFromSolverOptions = async () => {
    setIsRefreshingOptions(true);

    try {
      await refreshCases(effectiveMonthYear, true);
    } catch (error) {
      console.error("Failed to refresh cases from solver options", error);
    } finally {
      setIsRefreshingOptions(false);
    }
  };

  const monthOptions = useMemo(
    () =>
      Array.from({ length: 12 }, (_, index) => {
        const month = index + 1;
        return {
          month,
          label: new Date(0, month - 1).toLocaleString("de-DE", { month: "long" }),
        };
      }),
    [],
  );

  const casesForSelectedMonth = useMemo(() => {
    if (!effectiveMonthYear) return [];

    return availableCases.filter((unit) => unit.months.includes(effectiveMonthYear));
  }, [availableCases, effectiveMonthYear]);

  const updateMonthYear = (month: number, year: number) => {
    if (!Number.isInteger(month) || month < 1 || month > 12 || !Number.isInteger(year) || year < 1900 || year > 2100) {
      return;
    }

    const params = new URLSearchParams(searchParams.toString());

    params.set("monthYear", formatMonthYear(month, year));
    params.delete("caseIds");
    params.delete("caseId");

    router.push(`${pathname}?${params.toString()}`);
  };

  const handleMonthChange = (monthValue: string) => {
    updateMonthYear(Number(monthValue), selectedMonthYear.year);
  };

  const commitYearInput = () => {
    const year = Number(yearInput);
    if (!Number.isInteger(year) || year < 1900 || year > 2100) {
      setYearInput(String(selectedMonthYear.year));
      return;
    }

    updateMonthYear(selectedMonthYear.month, year);
  };

  const toggleCaseId = (caseId: number) => {
    const alreadySelected = selectedCaseIds.includes(caseId);

    const nextCaseIds = alreadySelected ? selectedCaseIds.filter((id) => id !== caseId) : [...selectedCaseIds, caseId];

    const params = new URLSearchParams(searchParams.toString());

    params.set("monthYear", effectiveMonthYear);

    if (nextCaseIds.length > 0) {
      params.set("caseIds", nextCaseIds.join(","));

      // Keep old single-case value for old pages/backend compatibility
      params.set("caseId", String(nextCaseIds[0]));
    } else {
      params.delete("caseIds");
      params.delete("caseId");
    }

    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="flex w-full max-w-[520px] flex-wrap items-center gap-2">
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-sm text-muted-foreground">Monat:</span>

        <Select
          value={effectiveMonthYear ? String(selectedMonthYear.month) : undefined}
          onValueChange={handleMonthChange}
          disabled={disabled}
        >
          <SelectTrigger className="w-[132px]">
            <SelectValue placeholder="Wähle Monat" />
          </SelectTrigger>

          <SelectContent className="max-h-[240px] overflow-y-auto">
            {monthOptions.map((option) => (
              <SelectItem key={option.month} value={String(option.month)}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="number"
          inputMode="numeric"
          min={1900}
          max={2100}
          value={yearInput}
          onChange={(event) => setYearInput(event.target.value)}
          onBlur={commitYearInput}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.currentTarget.blur();
            }
          }}
          disabled={disabled}
          aria-label="Jahr"
          className="h-8 w-[82px]"
        />
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {effectiveMonthYear && (
          <DropdownMenu open={isCasesOpen} onOpenChange={setIsCasesOpen}>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="h-8 w-[128px] justify-between px-2 text-sm"
                disabled={disabled || isLoading}
              >
                <span>Cases ({casesForSelectedMonth.length})</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${isCasesOpen ? "rotate-180" : ""}`} />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-[128px] max-h-40 overflow-y-auto">
              {casesForSelectedMonth.map((unit) => (
                <DropdownMenuCheckboxItem
                  key={unit.unitId}
                  checked={selectedCaseIds.includes(unit.unitId)}
                  disabled={disabled || isLoading}
                  onSelect={(event) => event.preventDefault()}
                  onCheckedChange={() => toggleCaseId(unit.unitId)}
                >
                  Case {unit.unitId}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={disabled || isLoading || isRefreshingOptions || !effectiveMonthYear}
          onClick={refreshCasesFromSolverOptions}
          aria-label="Cases vom Backend aktualisieren"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshingOptions ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <div className="hidden shrink-0">
        <Button size="sm" disabled={disabled || isLoading} onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <FetchCaseDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        initialCaseId={undefined}
        onFetched={(_, my) => {
          refreshCases();

          const params = new URLSearchParams(searchParams.toString());
          params.set("monthYear", my);
          params.delete("caseIds");
          params.delete("caseId");

          router.push(`${pathname}?${params.toString()}`);
        }}
      />
    </div>
  );
}
