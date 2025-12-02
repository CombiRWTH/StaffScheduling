export interface SolutionData {
  variables: Record<string, number>
  employees: Employee[]
  shifts: Shift[]
  days: Date[]
  stats: Stats
  fulfilledDayOffCells: Set<string>
  fulfilledShiftWishCells: Set<string>
  allDayOffWishCells: Set<string>
  allShiftWishColors: Record<string, string[]>
}

export interface Employee {
  id: number
  name: string
  level: string
  target_working_time: number
  wishes: {
    shift_wishes: [number, string][]
    day_off_wishes: number[]
  }
  unavailable_days?: number[]
  unavailable_shifts?: Record<number, string[]>
}

export interface Shift {
  id: number
  name: string
  abbreviation: string
  color: string
  duration: number
  is_exclusive: boolean
}

export interface Stats {
  forward_rotation_violations: number
  consecutive_working_days_gt_5: number
  no_free_weekend: number
  consecutive_night_shifts_gt_3: number
  total_overtime_hours: number
  no_free_days_around_weekend: number
  not_free_after_night_shift: number
  violated_wish_total: number
}

export function parseSolutionFile(jsonData: any): SolutionData {
  const variables = jsonData.variables || {}
  const employees = jsonData.employees || []
  const shifts = jsonData.shifts || []

  

  const days = jsonData.days.map((day) => {return new Date(day)}) || []

  // Calculate statistics
  const stats = jsonData.stats|| {}//analyzeSchedule(variables, employees, shifts)
  // Calculate fulfilled wishes
  const fulfilledDayOffCells = new Set<string>()
  const fulfilledShiftWishCells = new Set<string>()
  const allDayOffWishCells = new Set<string>()
  const allShiftWishColors: Record<string, string[]> = {}

  employees.forEach((employee: Employee) => {
    days.forEach((day) => {
      const dateStr = day.toISOString().split("T")[0]
      const cellKey = `${employee.id}-${dateStr}`

      // Day off wishes
      if (employee.wishes.day_off_wishes.includes(day.getDate())) {
        allDayOffWishCells.add(cellKey)

        // Check if any shift is assigned
        const hasShift = shifts.some((shift: Shift) => {
          const key = `(${employee.id}, '${dateStr}', ${shift.id})`
          return variables[key] === 1
        })

        if (!hasShift) {
          fulfilledDayOffCells.add(cellKey)
        }
      }

      // Shift wishes
      const shiftWishes = employee.wishes.shift_wishes.filter((w) => w[0] === day.getDate())
      if (shiftWishes.length > 0) {
        const colors = shiftWishes
          .map((w) => {
            const shift = shifts.find((s: Shift) => s.abbreviation === w[1])
            return shift?.color
          })
          .filter(Boolean) as string[]

        if (colors.length > 0) {
          allShiftWishColors[cellKey] = colors
        }

        // Check if none of the wished shifts are assigned
        const hasWishedShift = shiftWishes.some((w) => {
          const shift = shifts.find((s: Shift) => s.abbreviation === w[1])
          if (!shift) return false
          const key = `(${employee.id}, '${dateStr}', ${shift.id})`
          return variables[key] === 1
        })

        if (!hasWishedShift && !employee.wishes.day_off_wishes.includes(day.getDate())) {
          fulfilledShiftWishCells.add(cellKey)
        }
      }
    })
  })
  console.log({
    variables,
    employees,
    shifts,
    days,
    stats,
    fulfilledDayOffCells,
    fulfilledShiftWishCells,
    allDayOffWishCells,
    allShiftWishColors,
  })
  return {
    variables,
    employees,
    shifts,
    days,
    stats,
    fulfilledDayOffCells,
    fulfilledShiftWishCells,
    allDayOffWishCells,
    allShiftWishColors,
  }
}

function analyzeSchedule(variables: Record<string, number>, employees: Employee[], shifts: Shift[]): Stats {
  const employeeSchedules: Record<number, Record<string, number>> = {}
  const shiftDurationMap: Record<number, number> = {}

  shifts.forEach((shift) => {
    shiftDurationMap[shift.id] = shift.duration
  })

  // Parse variables into employee schedules
  Object.entries(variables).forEach(([key, value]) => {
    if (value !== 1) return
    const match = key.match(/$$(\d+), '([\d-]+)', (\d+)$$/)
    if (match) {
      const empId = Number.parseInt(match[1])
      const date = match[2]
      const shiftId = Number.parseInt(match[3])

      if (!employeeSchedules[empId]) {
        employeeSchedules[empId] = {}
      }
      employeeSchedules[empId][date] = shiftId
    }
  })

  let forwardRotationViolations = 0
  let consecutiveWorkingDaysGt5 = 0
  let noFreeWeekend = 0
  let consecutiveNightShiftsGt3 = 0
  let totalOvertimeHours = 0
  let noFreeDaysAroundWeekend = 0
  let notFreeAfterNightShift = 0
  let violatedWishTotal = 0

  employees.forEach((emp) => {
    const schedule = employeeSchedules[emp.id] || {}
    const dates = Object.keys(schedule).sort()
    const shiftIds = dates.map((d) => schedule[d])

    // Forward rotation violations
    const validShifts = shiftIds.filter((s) => [0, 2, 3].includes(s))
    for (let i = 0; i < validShifts.length - 1; i++) {
      if (validShifts[i + 1] < validShifts[i]) {
        forwardRotationViolations++
      }
    }

    // Consecutive working days > 5
    let streak = 1
    for (let i = 1; i < dates.length; i++) {
      const prevDate = new Date(dates[i - 1])
      const currDate = new Date(dates[i])
      const dayDiff = Math.floor((currDate.getTime() - prevDate.getTime()) / (1000 * 60 * 60 * 24))

      if (dayDiff === 1) {
        streak++
      } else {
        if (streak > 5) consecutiveWorkingDaysGt5++
        streak = 1
      }
    }
    if (streak > 5) consecutiveWorkingDaysGt5++

    // No free weekend
    const weekendDays = dates.filter((d) => {
      const day = new Date(d).getDay()
      return day === 0 || day === 6
    })
    if (weekendDays.length > 0) {
      noFreeWeekend++
    }

    // Consecutive night shifts > 3
    let nightStreak = 0
    shiftIds.forEach((s) => {
      if (s === 2) {
        nightStreak++
      } else {
        if (nightStreak > 3) consecutiveNightShiftsGt3++
        nightStreak = 0
      }
    })
    if (nightStreak > 3) consecutiveNightShiftsGt3++

    // Overtime
    const actualMinutes = shiftIds.reduce((sum, s) => sum + (shiftDurationMap[s] || 0), 0)
    const targetMinutes = emp.target_working_time
    const overtime = Math.max((actualMinutes - targetMinutes) / 60, 0)
    totalOvertimeHours += overtime

    // No free days around weekend
    dates.forEach((d) => {
      const date = new Date(d)
      const day = date.getDay()
      const nextDate = new Date(date)
      nextDate.setDate(nextDate.getDate() + 1)
      const nextDateStr = nextDate.toISOString().split("T")[0]

      if ((day === 5 || day === 6) && schedule[nextDateStr]) {
        noFreeDaysAroundWeekend++
      }
    })

    // Not free after night shift (48 hours)
    dates.forEach((d) => {
      if (schedule[d] === 2) {
        const date = new Date(d)
        for (let i = 1; i <= 2; i++) {
          const futureDate = new Date(date)
          futureDate.setDate(futureDate.getDate() + i)
          const futureDateStr = futureDate.toISOString().split("T")[0]
          if (schedule[futureDateStr] !== undefined) {
            notFreeAfterNightShift++
            break
          }
        }
      }
    })

    // Violated wishes
    emp.wishes.day_off_wishes.forEach((wishDay) => {
      const worked = dates.some((d) => new Date(d).getDate() === wishDay)
      if (worked) violatedWishTotal++
    })

    emp.wishes.shift_wishes.forEach(([wishDay, wishAbbr]) => {
      const date = dates.find((d) => new Date(d).getDate() === wishDay)
      if (date) {
        const assignedShift = shifts.find((s) => s.id === schedule[date])
        if (assignedShift?.abbreviation === wishAbbr) {
          violatedWishTotal++
        }
      }
    })
  })

  return {
    forward_rotation_violations: forwardRotationViolations,
    consecutive_working_days_gt_5: consecutiveWorkingDaysGt5,
    no_free_weekend: noFreeWeekend,
    consecutive_night_shifts_gt_3: consecutiveNightShiftsGt3,
    total_overtime_hours: Math.round(totalOvertimeHours * 100) / 100,
    no_free_days_around_weekend: noFreeDaysAroundWeekend,
    not_free_after_night_shift: notFreeAfterNightShift,
    violated_wish_total: violatedWishTotal,
  }
}
