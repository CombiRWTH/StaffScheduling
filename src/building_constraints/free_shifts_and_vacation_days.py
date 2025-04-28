import json

def load_free_shifts_and_vacation_days(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def add_free_shifts_and_vacatian_days(model, employees, shifts, constraints, num_days, num_shifts):
    name_to_index = {employee['name']: idx for idx, employee in enumerate(employees)}

    if 'time_off' in constraints:
        for request in constraints['time_off']:
            employeeidx = name_to_index[request['name']]
            if "days_off" in request:
                for day in request['days_off']:
                    for s in range(num_shifts):
                        model.Add(shifts[(employeeidx, day, s)] == 0)
                    model.Add(shifts[(employeeidx, day, 2)] == 0) # no night shift before vacation

            if "shifts_off" in request:
                for shift in request["shifts_off"]:
                    model.Add(shifts[(employeeidx, shift[0], shift[1])] == 0)
