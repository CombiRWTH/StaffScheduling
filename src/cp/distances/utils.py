import json


def convert_solution_to_shiftsets(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    variables = data.get("variables", {})

    shifts = {}

    for key, value in variables.items():
        if value != 1:
            continue
        if key.startswith("e:"):
            continue

        try:
            employee, day, shift = eval(key)
        except Exception as e:
            print(f"Error while parsing {key}: {e}")
            continue

        shifts.setdefault((day, shift), set()).add(employee)

    return shifts
