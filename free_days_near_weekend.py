from ortools.sat.python import cp_model

def free_days_near_weekend(model, shifts, num_days, num_persons, num_shifts, shift_id_map):
    """
    Prefer free days next to the weekend for better rest.
    
    Args:
        model: cp_model instance.
        shifts: 3D list [p][d][s] of BoolVars indicating assignments.
        num_days: Total number of days.
        num_persons: Total number of staff members.
        num_shifts: Total number of shifts per day.
        shift_id_map: Dictionary mapping shift types to their index.
    """
    for p in range(num_persons):
        for d in range(1, num_days - 1):
            if d % 7 in [0, 6]:  # Assuming 0 = Monday ... 6 = Sunday
                for s in range(num_shifts):
                    model.Add(shifts[p][d - 1][s] == 0)
                    model.Add(shifts[p][d + 1][s] == 0)

