from ortools.sat.python import cp_model

def weekend_rhythm(model, shifts, num_days, num_persons, num_shifts, shift_id_map):
    """
    Try to establish a weekend rhythm (e.g. working or off both days).
    
    Args:
        model: cp_model instance.
        shifts: 3D list [p][d][s] of BoolVars indicating assignments.
        num_days: Total number of days.
        num_persons: Total number of staff members.
        num_shifts: Total number of shifts per day.
        shift_id_map: Dictionary mapping shift types to their index.
    """
    for p in range(num_persons):
        for d in range(0, num_days - 1, 7):  # Saturday = d+5, Sunday = d+6
            if d + 6 < num_days:
                for s in range(num_shifts):
                    model.Add(shifts[p][d + 5][s] == shifts[p][d + 6][s])

