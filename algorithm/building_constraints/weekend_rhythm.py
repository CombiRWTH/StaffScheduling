from ortools.sat.python import cp_model
import StateManager

def add_weekend_rhythm(model, employees, shifts, num_days, num_shifts):
    """
    Ensure employees have a consistent weekend rhythm (either work or off both Sat & Sun).
    """
    num_persons = len(employees)

    for p in range(num_persons):
        for d in range(0, num_days - 1, 7):
            saturday = d + 5
            sunday = d + 6
            if sunday < num_days:
                for s in range(num_shifts):
                    model.Add(shifts[(p, saturday, s)] == shifts[(p, sunday, s)])

    StateManager.state.constraints.append("Weekend Rhythm")
