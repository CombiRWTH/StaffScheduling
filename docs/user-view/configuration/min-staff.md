Currently, our application lacks a user-friendly interface for comfortably managing configurations. Instead, these settings are stored in a JSON file, which requires manual editing to make any changes.

### Minimum Number of Staff

To ensure that each shift is adequately staffed with qualified personnel, it is essential to set the minimum required number of staff members. This configuration can be changed in the file `cases/{case_id}/minimal_number_of_staff.json`.

The structure of this JSON file looks as follows:

```json
{
    "Azubi": {
        "Di": {
            "F": 1,
            "N": 0,
            "S": 1
        },
        ...
    },
    ...
}
```

In this example, the keys represent employee types (e.g., Azubi) and days of the week (e.g., Di for Tuesday, abbreveations here are in German). The values indicate the minimum required number of staff for different shifts:

- **F** for early shifts,
- **N** for night shifts, and
- **S** for late shifts.

To modify the minimum staffing requirements, simply update the numerical values corresponding to each shift type as needed.
