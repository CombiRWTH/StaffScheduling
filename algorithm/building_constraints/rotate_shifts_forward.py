from ortools.sat.python import cp_model

def rotate_shifts_forward(model, shifts, num_days, num_persons, num_shifts, shift_id_map):
    """
    Shifts should rotate forward (e.g., F -> S -> N or F -> S -> Off).
    
    Args:
        model: cp_model instance.
        shifts: 3D list [p][d][s] of BoolVars indicating assignments.
        num_days: Total number of days.
        num_persons: Total number of staff members.
        num_shifts: Total number of shifts per day.
        shift_id_map: Dictionary mapping shift types to their index.
    """
    f, s, n = shift_id_map["F"], shift_id_map["S"], shift_id_map["N"]
    for p in range(num_persons):
        for d in range(num_days - 1):
            model.AddImplication(shifts[p][d][n], shifts[p][d + 1][f].Not())
            model.AddImplication(shifts[p][d][s], shifts[p][d + 1][f].Not())

