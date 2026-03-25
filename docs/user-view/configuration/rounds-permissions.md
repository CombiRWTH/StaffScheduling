--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Configuration of Rounds (Visiten)

In our application, rounds, or Visiten, are a specific type of qualification that ensures certain employees are available to fulfill this important role during designated shifts. The configuration for rounds is managed within `general_settings.json` in the active case folder, typically:

- `cases/{case_id}/{MM_YYYY}/general_settings.json` for month-based cases
- `cases/{case_id}/general_settings.json` for non-month cases

The relevant section in the JSON file appears as follows:

```json
"qualifications": {
    "2963": [
      "rounds"
    ],
    "3868": [
      "rounds"
    ],
    "791": [
      "rounds"
    ]
}
```

In this structure, each personal key corresponds to an employee who has been assigned the qualification for rounds. The keys can be found in `employees.json` in the same case folder and are unique to each employee.

Currently, rounds are the only type of special qualification available in our system. The application has been designed to automatically ensure that at least one employee with the "rounds" qualification is scheduled for every early shift on weekdays.
