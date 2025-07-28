--8<--
user-view/list-of-conditions.md:min-number-of-staff-per-shift
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/min_staffing.py"
if min_staffing is not None:
    model.add(sum(potential_working_staff) == min_staffing)
else:
    model.add(sum(potential_working_staff) >= 0)
```

For each day, shift required skill level ("Azubi", ...) we gather all eligible employees, get the minimum number of staff defined in `cases/{case_id}/minimal_number_of_staff.json` and collect all the corresponding variables (`potential_working_staff`).
The sum of those (number of people working) needs be equal to the required number (`min_staffing`). If there is no required `min_staffing`, e.g. when there are additional special shifts (Z60), we dont restrict the solution space.
