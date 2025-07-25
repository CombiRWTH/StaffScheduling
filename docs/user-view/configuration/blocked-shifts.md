Currently, our application lacks a user-friendly interface for comfortably managing configurations. Instead, these settings are stored in a JSON file, which requires manual editing to make any changes.

### Blocked Shifts

Blocked shifts are used to manually restrict specific shifts for individual employees based on their availability. For example, you may want to indicate that an employee is unavailable every Thursday, not allowed to work night shifts, or only permitted to work night shifts. This is a hard constraint.

These configurations can be modified in the file named `cases/{case_id}/wishes_and_blocked.json`. The structure of this file looks as follows:

```json
{
    "blocked_days": [
        1,
        2
    ],
    "blocked_shifts": [
        [
            25,
            "F"
        ]
    ],
    "firstname": "Janett",
    "key": 791,
    "name": "Branz",
    "wish_days": [],
    "wish_shifts": []
}
```

To add a blocked day, just add the number to the list; to add a blocked shift, add a list with two entries `[day, german shift abbreviation]` to `"blocked_shifts"`.
