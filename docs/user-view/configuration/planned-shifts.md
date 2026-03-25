--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Planned Shifts

Planned shifts refer to shifts that have already been assigned in TimeOffice, including special shifts such as "Sonderdienst Z60." These assignments can be directly managed within the TimeOffice system.

In the full version of our application, the file containing planned shifts is automatically generated and stored in `free_shifts_and_vacation_days.json` in the active case folder, typically:

- `cases/{case_id}/{MM_YYYY}/free_shifts_and_vacation_days.json` for month-based cases
- `cases/{case_id}/free_shifts_and_vacation_days.json` for non-month cases

In contrast, users of the light version can modify this file as needed.

The structure of this JSON file includes entries for each employee, as shown below:

```json
{
      "firstname": "Janett",
      "forbidden_days": [],
      "key": 791,
      "name": "Branz",
      "planned_shifts": [
        [
          5,
          "Z60"
        ]
      ],
      "vacation_days": []
    },
```

In this example, the `planned_shifts` array indicates any shifts that have been assigned to the employee. It is important to note that a shift assigned in the `planned_shifts` section serves as a hard constraint, meaning that it must be adhered to when scheduling other shifts.

By effectively managing planned shifts, organizations can ensure proper staffing levels and compliance with existing commitments.
