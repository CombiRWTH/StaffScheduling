Currently, our application lacks a user-friendly interface for comfortably managing configurations. Instead, these settings are stored in a JSON file, which requires manual editing to make any changes.

### Adding or Deleting Employees

Employee information is stored in the file located at `cases/{case_id}/employees.json`. Each employee entry follows this structure:

```json
{
    "firstname": "Annelene",
    "key": 6928,
    "name": "Izzo",
    "type": "Medizinische/r Fachangestellte/r (81102-004)"
}
```

To **add an employee**, create a new JSON object containing the required fields for each employee. Assign a unique key to each employee, as this is essential for identification within the system.

To **delete an employee**, locate their entry in the `employees.json` file and remove the corresponding JSON object. Be cautious when deleting entries.
