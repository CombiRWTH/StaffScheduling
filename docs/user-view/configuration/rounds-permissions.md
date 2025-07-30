--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Configuration of Rounds (Visiten)

In our application, rounds, or Visiten, are a specific type of qualification that ensures certain employees are available to fulfill this important role during designated shifts. The configuration for rounds is managed within the `cases/{case_id}/general_settings.json` file, where special qualifications are defined.

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

In this structure, each personal key corresponds to an employee who has been assigned the qualification for rounds. The personal keys can be found in `cases/{case_id}/employees.json` and are unique to each employee.

Currently, rounds are the only type of special qualification available in our system. The application has been designed to automatically ensure that at least one employee with the "rounds" qualification is scheduled for every early shift on weekdays.
