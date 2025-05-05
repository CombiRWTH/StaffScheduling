# StaffScheduling

# Output Format

---

## 1. Single Solution Representation

Each assignment in a solution is represented by a triple `(n, d, s)` where:

* `n` (employee index): An integer indicating the employee.
* `d` (day index): An integer indicating the day in the scheduling horizon.
* `s` (shift index): An integer indicating the shift within the day (e.g., 0, 1, 2).

A value of `1` indicates that the employee `n` works shift `s` on day `d`, while `0` means they do not.

```json
{
  "(n, d, s)": 0|1,
  ...
}
```

For example, for one employee on day 2 with shift 0:

```json
"(0, 2, 0)": 1
```

---

## 2. General `found_solution` Folder Structure

Each JSON file in the `found_solution` folder follows this structure:

```json
{
  "caseID": <integer>,
  "employees": {
    "name_to_index": {
      "<EmployeeName>": <index>,
      ...
    }
  },
  "constraints": [
    "<Constraint1>",
    "<Constraint2>",
    ...
  ],
  "numOfSolutions": <integer>,
  "givenSolutionLimit": <integer>,
  "solutions": [
    {
      "(0, 0, 0)": 0,
      "(0, 2, 2)": 1,
      "(0, 5, 0)": 1,
      "(0, 6, 1)": 1,
      ...
    },
    ...
  ]
}
```


