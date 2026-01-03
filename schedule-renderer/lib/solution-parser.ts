
export function parseSolutionFile(jsonData: any): SolutionData {
  const variables = jsonData.variables || {}
  const employees = jsonData.employees || []
  const shifts = jsonData.shifts || []



  const days = jsonData.days.map((day) => {return new Date(day)}) || []

  // Calculate statistics
  const stats = jsonData.stats|| {}//analyzeSchedule(variables, employees, shifts)
  // Calculate fulfilled wishes
  const fulfilledDayOffCells = jsonData.fulfilled_day_off_cells || []
  const fulfilledShiftWishCells = jsonData.fulfilled_shift_wish_cells || []
  const allDayOffWishCells = jsonData.all_day_off_wish_cells || []
  const allShiftWishColors: Record<string, string[]> = jsonData.all_shift_wish_colors || {}

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
