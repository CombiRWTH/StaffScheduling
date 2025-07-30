--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

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

To **add an employee**, create a new JSON object with the appropriate fields for each employee you wish to include. Ensure that you assign a unique key for each employee, as this is essential for identification within the system.

To **delete an employee**, locate their entry in the `employees.json` file and remove the corresponding JSON object. Be cautious when deleting entries.
