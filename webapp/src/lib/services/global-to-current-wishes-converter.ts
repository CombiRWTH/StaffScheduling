import {WishesAndBlockedEmployee} from "@/entities/models/wishes-and-blocked.model";
import {AvailabilityEmployee} from "@/entities/models/availability.model";

export function getDaysByWeekday(year?: number, month?: number): number[][] {
    const today = new Date();
    const y = typeof year === 'number' ? year : today.getFullYear();
    const m = typeof month === 'number' ? month : today.getMonth() + 1; // 1-12

    if (m < 1 || m > 12) throw new RangeError('month must be between 1 and 12');

    // new Date(y, m, 0) returns the last day of the requested month when month is in the 1-12 range.
    const daysInMonth = new Date(y, m, 0).getDate();

    // Result: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
    const result: number[][] = Array.from({length: 7}, () => []);

    for (let d = 1; d <= daysInMonth; d++) {
        const jsWeekday = new Date(y, m - 1, d).getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        const index = (jsWeekday + 6) % 7; // maps 1->0 (Monday) ... 0->6 (Sunday)
        result[index].push(d);
    }

    return result;
}

/**
 * Generates monthly wishes and blocked data from weekly data.
 * Therefore, the weekdays in the weekly data are expanded to actual days in the month.
 * @param weeklyEmployee
 * @param year
 * @param month
 */
export function generateMonthlyDataFromWeeklyData(weeklyEmployee: WishesAndBlockedEmployee, year?: number, month?: number): WishesAndBlockedEmployee {
    const daysByWeekday = getDaysByWeekday(year, month);
    const monthlyEmployee: WishesAndBlockedEmployee = {
        key: weeklyEmployee.key,
        firstname: weeklyEmployee.firstname,
        name: weeklyEmployee.name,
        wish_days: [],
        wish_shifts: [],
        work_days: [],
        work_shifts: [],
        blocked_days: [],
        blocked_shifts: []
    };

    // Expand weekly settings into concrete calendar days.
    (weeklyEmployee.wish_days ?? []).forEach(weekday => {
        if (weekday >= 1 && weekday <= 7) {
            monthlyEmployee.wish_days.push(...daysByWeekday[weekday - 1]);
        }
    });
    (weeklyEmployee.work_days ?? []).forEach(weekday => {
        if (weekday >= 1 && weekday <= 7) {
            monthlyEmployee.work_days.push(...daysByWeekday[weekday - 1]);
        }
    });
    (weeklyEmployee.blocked_days ?? []).forEach(weekday => {
        if (weekday >= 1 && weekday <= 7) {
            monthlyEmployee.blocked_days.push(...daysByWeekday[weekday - 1]);
        }
    });

    // Expand weekly shift settings into concrete day-shift pairs.
    (weeklyEmployee.wish_shifts ?? []).forEach(([weekday, shift]) => {
        if (weekday >= 1 && weekday <= 7) {
            daysByWeekday[weekday - 1].forEach(day => {
                monthlyEmployee.wish_shifts.push([day, shift]);
            });
        }
    });
    (weeklyEmployee.work_shifts ?? []).forEach(([weekday, shift]) => {
        if (weekday >= 1 && weekday <= 7) {
            daysByWeekday[weekday - 1].forEach(day => {
                monthlyEmployee.work_shifts.push([day, shift]);
            });
        }
    });
    (weeklyEmployee.blocked_shifts ?? []).forEach(([weekday, shift]) => {
        if (weekday >= 1 && weekday <= 7) {
            daysByWeekday[weekday - 1].forEach(day => {
                monthlyEmployee.blocked_shifts.push([day, shift]);
            });
        }
    });

    // Ensure canonical ordering: by day asc, then by shift (F, S, N)
    const SHIFT_ORDER = ['F', 'S', 'N'];
    const shiftPriority = (s: string) => {
        const idx = SHIFT_ORDER.indexOf(s);
        return idx === -1 ? 999 : idx;
    };

    monthlyEmployee.wish_shifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));
    monthlyEmployee.work_shifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));
    monthlyEmployee.blocked_shifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));

    // dedupe (same day + same shift)
    const dedupe = (arr: [number, string][]) => arr.filter((v, i, a) => i === 0 || !(v[0] === a[i - 1][0] && v[1] === a[i - 1][1]));
    monthlyEmployee.wish_shifts = dedupe(monthlyEmployee.wish_shifts);
    monthlyEmployee.work_shifts = dedupe(monthlyEmployee.work_shifts);
    monthlyEmployee.blocked_shifts = dedupe(monthlyEmployee.blocked_shifts);

    return monthlyEmployee;
}

export function generateMonthlyAvailabilityFromWeeklyData(
    weeklyEmployee: AvailabilityEmployee,
    year?: number,
    month?: number
): AvailabilityEmployee {
    const daysByWeekday = getDaysByWeekday(year, month);

    const expandWeekdays = (weekdays: number[]) => Array.from(
        new Set(
            weekdays.flatMap((weekday) => (
                weekday >= 1 && weekday <= 7 ? daysByWeekday[weekday - 1] : []
            ))
        )
    ).sort((a, b) => a - b);

    const expandShiftWeekdays = (weekdayShifts: [number, string][]) => {
        const shifts = weekdayShifts.flatMap(([weekday, shift]) => (
            weekday >= 1 && weekday <= 7
                ? daysByWeekday[weekday - 1].map((day): [number, string] => [day, shift])
                : []
        ));

        const SHIFT_ORDER = ['F', 'S', 'N'];
        const shiftPriority = (shift: string) => {
            const index = SHIFT_ORDER.indexOf(shift);
            return index === -1 ? 999 : index;
        };

        shifts.sort((a, b) => a[0] - b[0] || shiftPriority(a[1]) - shiftPriority(b[1]));

        return shifts.filter((shift, index, sortedShifts) =>
            index === 0 || !(shift[0] === sortedShifts[index - 1][0] && shift[1] === sortedShifts[index - 1][1])
        );
    };

    return {
        key: weeklyEmployee.key,
        firstname: weeklyEmployee.firstname,
        name: weeklyEmployee.name,
        unavailability_days: expandWeekdays(weeklyEmployee.unavailability_days ?? []),
        unavailability_shifts: expandShiftWeekdays(weeklyEmployee.unavailability_shifts ?? []),
    };
}
