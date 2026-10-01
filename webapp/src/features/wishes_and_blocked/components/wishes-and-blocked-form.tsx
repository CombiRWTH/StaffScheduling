"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { useState } from "react";
import { DayData, InteractiveCalendar } from "@/components/InteractiveCalendar";
import { Calendar as CalendarIcon, User } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useSearchParams } from "next/navigation";
import { parseMonthYear } from "@/lib/utils/case-utils";
import { EmployeeSelector } from "@/components/employee-selector";
import { Employee } from "@/entities/models/employee.model";

const wishesAndBlockedSchema = z.object({
  employeeKey: z.number().min(1, {
    message: "Bitte wähle einen Mitarbeiter aus.",
  }),
});

type WishesAndBlockedFormValues = z.infer<typeof wishesAndBlockedSchema>;

interface WishesAndBlockedFormProps {
  employee?: WishesAndBlockedEmployee;
  onSubmit: (data: WishesAndBlockedEmployee) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  excludedEmployeeKeys?: number[];
  isGlobal?: boolean;
  caseId?: number;
  monthYear?: string;
}

// Helper to convert WishesAndBlockedEmployee data to DayData format
function convertToDayData(
  year: number,
  month: number,
  wishDays: number[],
  wishShifts: [number, string][],
  workDays: number[],
  workShifts: [number, string][],
  blockedDays: number[],
  blockedShifts: [number, string][],
): DayData[] {
  const dayDataMap = new Map<number, DayData>();

  // Add wish days
  wishDays.forEach((day) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    dayDataMap.set(day, {
      date,
      categoryId: "wish",
      events: dayDataMap.get(day)?.events || [],
    });
  });

  // Add work days
  workDays.forEach((day) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const existing = dayDataMap.get(day);
    dayDataMap.set(day, {
      date,
      categoryId: "work",
      events: existing?.events || [],
    });
  });

  // Add blocked days
  blockedDays.forEach((day) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const existing = dayDataMap.get(day);
    dayDataMap.set(day, {
      date,
      categoryId: "blocked",
      events: existing?.events || [],
    });
  });

  // Add wish shifts as events
  wishShifts.forEach(([day, shiftCode]) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const existing = dayDataMap.get(day);
    const events = existing?.events || [];

    dayDataMap.set(day, {
      date,
      categoryId: existing?.categoryId,
      events: [
        ...events,
        {
          id: `${date}-wish-${shiftCode}-${Date.now()}`,
          title: shiftCode,
          categoryId: "wish-shift",
        },
      ],
    });
  });

  // Add work shifts as events
  workShifts.forEach(([day, shiftCode]) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const existing = dayDataMap.get(day);
    const events = existing?.events || [];

    dayDataMap.set(day, {
      date,
      categoryId: existing?.categoryId,
      events: [
        ...events,
        {
          id: `${date}-work-${shiftCode}-${Date.now()}`,
          title: shiftCode,
          categoryId: "work-shift",
        },
      ],
    });
  });

  // Add blocked shifts as events
  blockedShifts.forEach(([day, shiftCode]) => {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const existing = dayDataMap.get(day);
    const events = existing?.events || [];

    dayDataMap.set(day, {
      date,
      categoryId: existing?.categoryId,
      events: [
        ...events,
        {
          id: `${date}-blocked-${shiftCode}-${Date.now()}`,
          title: shiftCode,
          categoryId: "blocked-shift",
        },
      ],
    });
  });

  return Array.from(dayDataMap.values());
}

// Helper to convert DayData back to WishesAndBlockedEmployee format
function convertFromDayData(dayData: DayData[]): {
  wishDays: number[];
  wishShifts: [number, string][];
  workDays: number[];
  workShifts: [number, string][];
  blockedDays: number[];
  blockedShifts: [number, string][];
} {
  const wishDays: number[] = [];
  const wishShifts: [number, string][] = [];
  const workDays: number[] = [];
  const workShifts: [number, string][] = [];
  const blockedDays: number[] = [];
  const blockedShifts: [number, string][] = [];

  const SHIFT_ORDER = ["F", "S", "N"];
  const shiftPriority = (s: string) => {
    const idx = SHIFT_ORDER.indexOf(s);
    return idx === -1 ? 999 : idx;
  };

  dayData.forEach((data) => {
    const day = parseInt(data.date.split("-")[2], 10);

    if (data.categoryId === "wish") {
      wishDays.push(day);
    } else if (data.categoryId === "work") {
      workDays.push(day);
    } else if (data.categoryId === "blocked") {
      blockedDays.push(day);
    }

    data.events.forEach((event) => {
      if (event.categoryId === "wish-shift") {
        wishShifts.push([day, event.title]);
      } else if (event.categoryId === "work-shift") {
        workShifts.push([day, event.title]);
      } else if (event.categoryId === "blocked-shift") {
        blockedShifts.push([day, event.title]);
      }
    });
  });

  // Sort by day ASC, then by canonical shift order (F, S, N)
  wishShifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));
  workShifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));
  blockedShifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));

  // Remove duplicates (same day + same shift)
  const dedupePairs = (arr: [number, string][]) =>
    arr.filter((v, i, a) => i === 0 || !(v[0] === a[i - 1][0] && v[1] === a[i - 1][1]));
  const uniqueWishShifts = dedupePairs(wishShifts);
  const uniqueWorkShifts = dedupePairs(workShifts);
  const uniqueBlockedShifts = dedupePairs(blockedShifts);

  // Also sort days uniquely
  wishDays.sort((a, b) => a - b);
  workDays.sort((a, b) => a - b);
  blockedDays.sort((a, b) => a - b);

  return {
    wishDays: Array.from(new Set(wishDays)),
    wishShifts: uniqueWishShifts,
    workDays: Array.from(new Set(workDays)),
    workShifts: uniqueWorkShifts,
    blockedDays: Array.from(new Set(blockedDays)),
    blockedShifts: uniqueBlockedShifts,
  };
}

export function WishesAndBlockedForm({
  employee,
  onSubmit,
  onCancel,
  isSubmitting,
  excludedEmployeeKeys = [],
  isGlobal,
  caseId,
  monthYear,
}: WishesAndBlockedFormProps) {
  const searchParams = useSearchParams();
  const monthYearStr = monthYear ?? searchParams.get("monthYear") ?? "";
  const { month: urlMonth, year: urlYear } = monthYearStr
    ? parseMonthYear(monthYearStr)
    : { month: new Date().getMonth() + 1, year: new Date().getFullYear() };
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(() =>
    employee
      ? ({
          key: employee.key,
          firstname: employee.firstname,
          name: employee.name,
          type: "",
        } as Employee)
      : null,
  );

  const form = useForm<WishesAndBlockedFormValues>({
    resolver: zodResolver(wishesAndBlockedSchema),
    defaultValues: {
      employeeKey: employee?.key || 0,
    },
  });

  // Get year and month from URL params or use current date
  const year = urlYear;
  const month = urlMonth;

  // State for calendar data
  const [calendarData, setCalendarData] = useState<DayData[]>(() =>
    convertToDayData(
      year,
      month,
      employee?.wish_days || [],
      employee?.wish_shifts || [],
      employee?.work_days || [],
      employee?.work_shifts || [],
      employee?.blocked_days || [],
      employee?.blocked_shifts || [],
    ),
  );

  // Categories for day types (preferred day, blocked day)
  const dayCategories = [
    { id: "wish", name: "Gewünschter freier Tag", color: "#60a5fa" },
    { id: "work", name: "Gewünschte Arbeitstag", color: "#22c55e" },
    { id: "blocked", name: "Blockierter Tag", color: "#dc2626" },
  ];

  // Categories for shifts
  const eventCategories = [
    { id: "wish-shift", name: "Gewünschte freie Schicht", color: "#bfdbfe" },
    { id: "work-shift", name: "Gewünschte Arbeitsschicht", color: "#bbf7d0" },
    { id: "blocked-shift", name: "Blockierte Schicht", color: "#fecaca" },
  ];

  const handleFormSubmit = () => {
    if (!selectedEmployee) return;

    const { wishDays, wishShifts, workDays, workShifts, blockedDays, blockedShifts } = convertFromDayData(calendarData);

    onSubmit({
      key: selectedEmployee.key,
      firstname: selectedEmployee.firstname,
      name: selectedEmployee.name,
      wish_days: wishDays,
      wish_shifts: wishShifts,
      work_days: workDays,
      work_shifts: workShifts,
      blocked_days: blockedDays,
      blocked_shifts: blockedShifts,
    });
  };

  const handleEmployeeSelect = (emp: Employee | null) => {
    setSelectedEmployee(emp);
    form.setValue("employeeKey", emp?.key || 0);
  };

  const handleCalendarDataChange = (newData: DayData[]) => {
    setCalendarData(newData);
  };

  // Calculate statistics from calendar data
  const stats = convertFromDayData(calendarData);
  const wishDaysCount = stats.wishDays.length;
  const wishShiftsCount = stats.wishShifts.length;
  const workDaysCount = stats.workDays.length;
  const workShiftsCount = stats.workShifts.length;
  const blockedDaysCount = stats.blockedDays.length;
  const blockedShiftsCount = stats.blockedShifts.length;

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Employee Selection */}
          <Card className="min-w-0">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-5 w-5" />
                Mitarbeiter auswählen
              </CardTitle>
              <CardDescription>Suche und wähle einen Mitarbeiter aus der Mitarbeiterdatenbank</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="employeeKey"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mitarbeiter</FormLabel>
                    <FormControl>
                      <EmployeeSelector
                        value={field.value || undefined}
                        onSelect={handleEmployeeSelect}
                        disabled={!!employee || isSubmitting}
                        excludedKeys={employee ? [] : excludedEmployeeKeys}
                        caseId={caseId}
                        monthYear={monthYearStr}
                      />
                    </FormControl>
                    {employee && (
                      <FormDescription>Mitarbeiter können beim Bearbeiten nicht geändert werden.</FormDescription>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Summary Stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{wishDaysCount}</div>
                  <div className="text-xs text-muted-foreground">Gewünschte freie Tage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{wishShiftsCount}</div>
                  <div className="text-xs text-muted-foreground">Gewünschte freie Schichten</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{workDaysCount}</div>
                  <div className="text-xs text-muted-foreground">Gewünschte Arbeitstage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{workShiftsCount}</div>
                  <div className="text-xs text-muted-foreground">Gewünschte Arbeitsschichten</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{blockedDaysCount}</div>
                  <div className="text-xs text-muted-foreground">Blockierte Tage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">{blockedShiftsCount}</div>
                  <div className="text-xs text-muted-foreground">Blockierte Schichten</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Interactive Calendar */}
          <Card className="min-w-0">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CalendarIcon className="h-5 w-5" />
                {isGlobal ? `Wochenkalender` : `Monatskalender`}
              </CardTitle>
              <CardDescription>Klicke auf einen Tag, um Wünsche oder Blockierungen zu verwalten</CardDescription>
            </CardHeader>
            <CardContent>
              <InteractiveCalendar
                month={month}
                year={year}
                categories={dayCategories}
                eventCategories={eventCategories}
                initialDayData={calendarData}
                onDayDataChange={handleCalendarDataChange}
                maxVisibleEvents={3}
                showLegend={true}
                view={isGlobal ? "week" : "month"}
                allowedEventTitles={["F", "S", "N"]}
                wishShiftRules={[
                  {
                    categoryId: "wish",
                    eventCategoryId: "wish-shift",
                    eventTitles: ["F", "S", "N"],
                  },
                  {
                    categoryId: "work",
                    eventCategoryId: "work-shift",
                    eventTitles: ["F", "S", "N"],
                  },
                  {
                    categoryId: "blocked",
                    eventCategoryId: "blocked-shift",
                    eventTitles: ["F", "S", "N"],
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Abbrechen
          </Button>
          <Button type="submit" disabled={isSubmitting || (!employee && !selectedEmployee)}>
            {isSubmitting ? "Speichern..." : "Speichern"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
