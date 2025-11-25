def convert_solution_to_shiftsets(solution_dict):
    shifts = {}
    skipped_count = 0

    for key, value in solution_dict.items():
        if value != 1:
            continue

        if key.startswith("e:"):
            skipped_count += 1
            continue

        try:
            employee, day, shift = eval(key)
        except Exception as e:
            print(f"Fehler beim Parsen von Key '{key}': {e}")
            skipped_count += 1
            continue

        if (day, shift) not in shifts:
            shifts[(day, shift)] = set()
        shifts[(day, shift)].add(employee)

    # print(f"Übersprungene Keys: {skipped_count}")
    return shifts
