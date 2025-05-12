from ortools.sat.python import cp_model

def not_too_long_shifts(model, shifts, num_days, num_persons, num_shifts, shift_id_map):
    """
    Avoid assigning too many long shifts in a row.
    
    Args:
        model: cp_model instance.
        shifts: 3D list [p][d][s] of BoolVars indicating assignments.
        num_days: Total number of days.
        num_persons: Total number of staff members.
        num_shifts: Total number of shifts per day.
        shift_id_map: Dictionary mapping shift types to their index.
    """
    long_shift_idxs = [shift_id_map.get(k) for k in ["S", "N"] if k in shift_id_map]
    for p in range(num_persons):
        for d in range(num_days - 2):
            for s in long_shift_idxs:
                model.AddBoolOr([
                    shifts[p][d][s].Not(),
                    shifts[p][d + 1][s].Not(),
                    shifts[p][d + 2][s].Not()
                ])

