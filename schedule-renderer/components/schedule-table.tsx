"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

interface Employee {
  id: number
  name: string
  level: string
  target_working_time: number
  wishes: {
    shift_wishes: [number, string][]
    day_off_wishes: number[]
  }
}

interface Shift {
  id: number
  name: string
  abbreviation: string
  color: string
  duration: number
  is_exclusive: boolean
}

interface ScheduleTableProps {
  employees: Employee[]
  days: Date[]
  shifts: Shift[]
  variables: Record<string, number>
  fulfilledDayOffCells: [][]
  fulfilledShiftWishCells: [][]
  allDayOffWishCells: [][]
  allShiftWishColors: Record<string, string[]>
  className?: string
}

export function ScheduleTable({
  employees,
  days,
  shifts,
  variables,
  fulfilledDayOffCells,
  fulfilledShiftWishCells,
  allDayOffWishCells,
  allShiftWishColors,
  className,
}: ScheduleTableProps) {
  const [hoveredCell, setHoveredCell] = useState<string | null>(null)

  const getShiftForCell = (empId: number, day: Date): Shift | null => {
    const dateStr = day.toISOString().split("T")[0]
    for (const shift of shifts) {
      const key = `(${empId}, '${dateStr}', ${shift.id})`
      if (variables[key] === 1) {
        return shift
      }
    }
    return null
  }

  const isWeekend = (day: Date) => {
    const dayOfWeek = day.getDay()
    return dayOfWeek === 0 || dayOfWeek === 6
  }

  const unavailable = (employee: any, day: any, shift?: any) => {
    if (!shift) {
      return (
        employee.vacation_days.includes(day) ||
        employee.forbidden_days.includes(day)
      );
    }
    return (
      employee.vacation_shifts.some(
        ([d, s]: [number, string]) => d === day && s === shift.abbreviation
      ) ||
      employee.forbidden_shifts.some(
        ([d, s]: [number, string]) => d === day && s === shift.abbreviation
      )
    );
  };

  const getEmployeeStats = (employee: Employee) => {
    let totalMinutes = 0
    let totalShifts = 0

    days.forEach((day) => {
      const shift = getShiftForCell(employee.id, day)
      if (shift) {
        totalMinutes += shift.duration
        totalShifts++
      }
    })

    const actualHours = totalMinutes / 60
    const targetHours = employee.target_working_time / 60
    const hasOvertime = Math.abs(actualHours - targetHours) > 7.67

    return { actualHours, targetHours, totalShifts, hasOvertime }
  }

  return (
    <div className={cn("relative overflow-auto max-h-[800px]", className)}>
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-20 bg-card">
          <tr>
            <th className="sticky left-0 z-30 min-w-[160px] border-b border-r border-border bg-card p-3 text-left font-semibold text-foreground">
              Employee
            </th>
            {days.map((day, idx) => (
              <th
                key={idx}
                className={cn(
                  "border-b border-border p-3 text-center font-medium text-foreground min-w-[100px]",
                  isWeekend(day) && "bg-muted/30",
                )}
              >
                <div className="space-y-1">
                  <div className="font-semibold">
                    {day.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {day.toLocaleDateString("en-US", { weekday: "short" })}
                  </div>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => {
            const stats = getEmployeeStats(employee)
            return (
              <tr key={employee.id}>
                <td
                  className="sticky left-0 z-10 border-b border-r border-border bg-card p-0"
                >
                  <div className={cn(
                    "p-3 h-full w-full",
                    stats.hasOvertime && "bg-destructive/5"
                  )}>
                    <div className="space-y-1">
                      <div className="font-medium text-foreground">{employee.name}</div>
                      <div className="text-xs text-muted-foreground">{employee.level}</div>
                      <div className="mt-2 text-xs">
                        <div className="text-muted-foreground">{stats.totalShifts} shifts</div>
                        <div
                          className={cn("font-medium", stats.hasOvertime ? "text-destructive" : "text-muted-foreground")}
                        >
                          {stats.actualHours.toFixed(1)}h / {stats.targetHours.toFixed(1)}h
                        </div>
                      </div>
                    </div>
                  </div>
                </td>
                {days.map((day, dayIdx) => {
                  const shift = getShiftForCell(employee.id, day)
                  const dateStr = day.toISOString().split("T")[0]
                  const cellKey = `${employee.id}-${dateStr}`

                  const isDayOffFulfilled = fulfilledDayOffCells.some(
                    ([id, date]) => id === employee.id && date === dateStr
                  )
                  const isShiftWishFulfilled = fulfilledShiftWishCells.some(
                    ([id, date]) => id === employee.id && date === dateStr
                  )
                  const hasDayOffWish = allDayOffWishCells.some(
                    ([id, date]) => id === employee.id && date === dateStr
                  )
                  const shiftWishColors = allShiftWishColors[cellKey] || []

                  const isUnavailable = unavailable(employee, dayIdx);

                  return (
                    <td
  key={dayIdx}
  className={cn(
    "border-b border-border p-2 text-center relative",
    isWeekend(day) && "bg-muted/30",
    isDayOffFulfilled && "bg-amber-400/10",
    isShiftWishFulfilled && "bg-emerald-400/10",
    isUnavailable && "bg-rose-400/10",
    !shift && !isDayOffFulfilled && hasDayOffWish && "bg-rose-400/5",
  )}
>
  <div className="flex flex-col items-center gap-1">

    {/* --- UNAVAILABLE SHIFT CIRCLES (NEW) --- */}
    <div className="flex items-center gap-1 mb-1">
      {shifts.map((s) =>
        unavailable(employee, dayIdx, s) ? (
          <div
            key={s.id}
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: s.color }}
          />
        ) : null
      )}
    </div>

    {/* --- DAY-OFF WISH TRIANGLE + SHIFT-WISH DIAMONDS --- */}

      <div className="flex items-center gap-1 mb-1">
        {hasDayOffWish && (
          <div
            className="w-0 h-0 border-l-[4px] border-r-[4px] border-b-[6px]"
            style={{
              borderLeftColor: "transparent",
              borderRightColor: "transparent",
              borderBottomColor: "#b77c02",
            }}
          />
        )}
        {shiftWishColors.map((color, idx) => (
          <div
            key={idx}
            className="w-2 h-2"
            style={{
              backgroundColor: color,
              transform: "rotate(45deg)",
            }}
          />
        ))}
      </div>


    {/* --- SHIFT ASSIGNMENT --- */}
    {shift ? (
      <div
        className="rounded-md px-2 py-1.5 font-medium text-white w-full"
        style={{ backgroundColor: shift.color }}
      >
        {shift.abbreviation}
      </div>
    ) : (
      <div className="py-1.5" />
    )}
  </div>
</td>

                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
