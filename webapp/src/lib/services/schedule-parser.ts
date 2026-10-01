import {
    ScheduleEmployee,
    ScheduleSolution,
    ScheduleSolutionRaw,
    ScheduleStats,
    Shift
} from '@/entities/models/schedule.model';
import type {IScheduleParserService} from '@/application/ports/schedule-parser.service';

/**
 * Parses a raw schedule solution from the solver into a structured format
 * with calculated fulfilled wishes and other derived data.
 *
 * @param jsonData - Raw JSON data from the schedule solver
 * @returns Parsed schedule solution with calculated data
 */
export function parseSolutionFile(jsonData: ScheduleSolutionRaw): ScheduleSolution {
    const variables = jsonData.variables || {};
    const employees = (jsonData.employees || []).map((emp) => ({
        ...emp,
        vacation_days: emp.vacation_days || [],
        forbidden_days: emp.forbidden_days || [],
        vacation_shifts: emp.vacation_shifts || [],
        forbidden_shifts: emp.forbidden_shifts || [],
    }));
    const shifts = jsonData.shifts || [];
    const days = jsonData.days.map((day) => new Date(day));
    const stats = jsonData.stats || createEmptyStats();

    // Calculate fulfilled wishes
    const fulfilledDayOffCells = new Set<string>();
    const fulfilledShiftWishCells = new Set<string>();
    const allDayOffWishCells = new Set<string>();
    const allShiftWishColors: Record<string, string[]> = {};

    // Iterate over each employee and day to check wishes
    employees.forEach((employee: ScheduleEmployee) => {
        days.forEach((day) => {
            const dateStr = day.toISOString().split('T')[0];
            const cellKey = `${employee.id}-${dateStr}`;

            // Day off wishes
            if (employee.wishes.day_off_wishes.includes(day.getDate())) {
                allDayOffWishCells.add(cellKey);

                // Check if any shift is assigned
                const hasShift = shifts.some((shift: Shift) => {
                    const key = `(${employee.id}, '${dateStr}', ${shift.id})`;
                    return variables[key] === 1;
                });

                if (!hasShift) {
                    fulfilledDayOffCells.add(cellKey);
                }
            }

            // Shift wishes
            const shiftWishes = employee.wishes.shift_wishes.filter((w) => w[0] === day.getDate());
            if (shiftWishes.length > 0) {
                const colors = shiftWishes
                    .map((w) => {
                        // Find the shift by abbreviation
                        const shift = shifts.find((s: Shift) => s.abbreviation === w[1]);
                        return shift?.color;
                    })
                    .filter(Boolean) as string[];

                if (colors.length > 0) {
                    allShiftWishColors[cellKey] = colors;
                }

                // Check if none of the wished shifts are assigned
                const hasWishedShift = shiftWishes.some((w) => {
                    const shift = shifts.find((s: Shift) => s.abbreviation === w[1]);
                    if (!shift) return false;
                    const key = `(${employee.id}, '${dateStr}', ${shift.id})`;
                    return variables[key] === 1;
                });

                if (!hasWishedShift && !employee.wishes.day_off_wishes.includes(day.getDate())) {
                    fulfilledShiftWishCells.add(cellKey);
                }
            }
        });
    });

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
    };
}

/**
 * Creates an empty stats object with all values set to 0.
 */
function createEmptyStats(): ScheduleStats {
    return {
        forward_rotation_violations: 0,
        consecutive_working_days_gt_5: 0,
        no_free_weekend: 0,
        consecutive_night_shifts_gt_3: 0,
        total_overtime_hours: 0,
        no_free_days_around_weekend: 0,
        not_free_after_night_shift: 0,
        violated_wish_total: 0,
    };
}

/**
 * Gets the assigned shift for a specific employee and day.
 *
 * @param empId - Employee ID
 * @param day - Date to check
 * @param shifts - Array of available shifts
 * @param variables - Variable assignments from solver
 * @returns The assigned shift or null if no shift assigned
 */
export function getShiftForCell(
    empId: number,
    day: Date,
    shifts: Shift[],
    variables: Record<string, number>
): Shift | null {
    const dateStr = day.toISOString().split('T')[0];
    for (const shift of shifts) {
        const key = `(${empId}, '${dateStr}', ${shift.id})`;
        if (variables[key] === 1) {
            return shift;
        }
    }
    return null;
}

/**
 * Gets all assigned shifts for a specific employee and day.
 * Updated to support multiple shifts per cell.
 *
 * @param empId - Employee ID
 * @param day - Date to check
 * @param shifts - Array of available shifts
 * @param variables - Variable assignments from solver
 * @returns Array of assigned shifts (can be empty if no shifts assigned)
 */
export function getShiftsForCell(
    empId: number,
    day: Date,
    shifts: Shift[],
    variables: Record<string, number>
): Shift[] {
    const dateStr = day.toISOString().split('T')[0];
    const result: Shift[] = [];

    for (const shift of shifts) {
        const key = `(${empId}, '${dateStr}', ${shift.id})`;
        if (variables[key] === 1) {
            result.push(shift);
        }
    }

    return result;
}

/**
 * Checks if a date is a weekend (Saturday or Sunday).
 */
export function isWeekend(day: Date): boolean {
    const dayOfWeek = day.getDay();
    return dayOfWeek === 0 || dayOfWeek === 6;
}

/**
 * Calculates statistics for an employee's schedule.
 *
 * @param employee - The employee to calculate stats for
 * @param days - Array of dates in the schedule
 * @param shifts - Array of available shifts
 * @param variables - Variable assignments from solver
 * @returns Employee statistics including hours worked and overtime
 */
export function getEmployeeStats(
    employee: ScheduleEmployee,
    days: Date[],
    shifts: Shift[],
    variables: Record<string, number>
) {
    let totalMinutes = 0;
    let totalShifts = 0;

    days.forEach((day) => {
        const shiftsForDay = getShiftsForCell(employee.id, day, shifts, variables);
        shiftsForDay.forEach((shift) => {
            totalMinutes += shift.duration;
            totalShifts++;

        });
    });

    const factor = (1 - ([...new Set([...employee.vacation_days, ...employee.forbidden_days])].length) / days.length)
    const a = totalMinutes + employee.hidden_actual_working_time
    const b = employee.target_working_time * factor

    if (employee.actual_working_time >= employee.target_working_time * factor - 460) {
        return {actualHours: a / 60, targetHours: b / 60, totalShifts, hasOvertime: false};
    }

    const hasOvertime = Math.abs(a - b) > 460;

    return {actualHours: a / 60, targetHours: b / 60, totalShifts, hasOvertime}
}

/**
 * Class-based adapter that implements IScheduleParserService by delegating to
 * the standalone `parseSolutionFile` helper above.
 * Register this in the DI container as the concrete implementation of
 * IScheduleParserService.
 */
export class ScheduleParserService implements IScheduleParserService {
    parseSolution(jsonData: ScheduleSolutionRaw): ScheduleSolution {
        return parseSolutionFile(jsonData);
    }
}
