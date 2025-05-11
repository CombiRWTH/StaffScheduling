# Data format of each constraint
Most of the constraint need some kind of input. This input is save in `cases/i/`
and stored as `json` file.
The person who implements a new constraint does decide how the constraint
is formulated / what the data format should look like, but is also
responseable for its documentation.

## Minimal Number of Staff
For each type of staff there is a dictornary with each day of the week, providing the required number of staff per shift. The shift keys are `"F"`, `"S"` and `"N"`, for the german terms "Frühschicht", "Spätschicht", "Nachtschicht".
The weekdays are also in german and abbreviated.
**Example:**
```json
{
  "Fachkraft": {
    "Mo": {"F": 1, "S": 1, "N": 1},
    "Di": {"F": 1, "S": 4, "N": 3},
    "Mi": {"F": 3, "S": 3, "N": 1},
    "Do": {"F": 2, "S": 1, "N": 1},
    "Fr": {"F": 1, "S": 2, "N": 1},
    "Sa": {"F": 2, "S": 1, "N": 3} ,
    "So": {"F": 1, "S": 2, "N": 1}
  },
  "Hilfskraft" : {
    "Mo": {"F": 1, "S": 1, "N": 1},
    "Di": {"F": 1, "S": 1, "N": 1},
    "Mi": {"F": 1, "S": 1, "N": 1},
    "Do": {"F": 1, "S": 1, "N": 1},
    "Fr": {"F": 1, "S": 1, "N": 1},
    "Sa": {"F": 1, "S": 1, "N": 1} ,
    "So": {"F": 1, "S": 1, "N": 1}
  },
  "Azubi" : {
    "Mo": {"F": 1, "S": 1, "N": 1},
    "Di": {"F": 1, "S": 1, "N": 1},
    "Mi": {"F": 1, "S": 1, "N": 1},
    "Do": {"F": 1, "S": 1, "N": 1},
    "Fr": {"F": 1, "S": 1, "N": 1},
    "Sa": {"F": 1, "S": 1, "N": 1} ,
    "So": {"F": 1, "S": 1, "N": 1}
  }
}
```
