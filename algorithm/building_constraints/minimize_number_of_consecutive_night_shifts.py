from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Minimize number of consecutive night shifts"


def add_minimize_number_of_consecutive_night_shifts(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days,
) -> None:
    # penalties increases for longer night shift phases
    weights = {
        2: 1,
        3: 3,
        4: 6,
        5: 10,  # 5 or more
    }

    penalties = []

    # this is currently not ideal
    # a night shift of length 4 is also counted (multiple times) in night shift
    # if len 2 and 3. 
    # This counteracts to the defined weights.
    for n in range(len(employees)):
        for d in range(num_days - 1):  # for length 2
            nights = [shifts[(n, d + i, 2)] for i in range(2)]
            var = model.NewBoolVar(f"night_phase_2_n{n}_d{d}")
            model.AddBoolAnd(nights).OnlyEnforceIf(var)
            model.AddBoolOr([n.Not() for n in nights]).OnlyEnforceIf(var.Not())
            penalties.append((var, weights[2]))

        for d in range(num_days - 2):  # for length 3
            nights = [shifts[(n, d + i, 2)] for i in range(3)]
            var = model.NewBoolVar(f"night_phase_3_n{n}_d{d}")
            model.AddBoolAnd(nights).OnlyEnforceIf(var)
            model.AddBoolOr([n.Not() for n in nights]).OnlyEnforceIf(var.Not())
            penalties.append((var, weights[3]))

        for d in range(num_days - 3):  # for length 4
            nights = [shifts[(n, d + i, 2)] for i in range(4)]
            var = model.NewBoolVar(f"night_phase_4_n{n}_d{d}")
            model.AddBoolAnd(nights).OnlyEnforceIf(var)
            model.AddBoolOr([n.Not() for n in nights]).OnlyEnforceIf(var.Not())
            penalties.append((var, weights[4]))

        for d in range(num_days - 4):  # for length 5+
            nights = [shifts[(n, d + i, 2)] for i in range(5)]
            var = model.NewBoolVar(f"night_phase_5plus_n{n}_d{d}")
            model.AddBoolAnd(nights).OnlyEnforceIf(var)
            model.AddBoolOr([n.Not() for n in nights]).OnlyEnforceIf(var.Not())
            penalties.append((var, weights[5]))

    StateManager.state.objectives.append(
        (sum(weight * var for var, weight in penalties), NAME_OF_CONSTRAINT)
    )
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
