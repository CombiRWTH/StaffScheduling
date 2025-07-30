# File: `employees_types.json`

### Description

This file contains three lists of interal job titles that are mapped to the job categories / level
that we use: "Azubi", "Fachkraft" and "Hilfskraft".

### Structure

```jsonc
{
  "Azubi": "list",          // List of all internal job titles that are seen as "Azubi"
  "Fachkraft": "list",      // List of all internal job titles that are seen as "Fachkraft"
  "Hilfskraft": "list"      // List of all internal job titles that are seen as "Hilfskraft"
}
```

---

# File: `employees.json`

### Description

This file contains a list of all employees within our planning unit (Planungseinheit), including their `key` (internal ID), `personnel_number`, `name`, `firstname`, and `title` (job title).

### Structure

```jsonc
{
  "employees": [             // List of all employees
    {
      "key": "int",          // Internal primary key ID
      "firstname": "string", // First name of the employee
      "name": "string",      // Last name of the employee
      "type": "string"       // Job title (may include an intern classification code)
    }
  ]
}
```

---

# File: `free_shifts_and_vacation_days.json`

### Description

This file contains the list of all employees within our PE (Planungseinheit) which already have submitted vacation days or shifts within TimeOffice or days that are either crossed off or worked within another PE. If an employee is not working somewehere else or has blocked days then an empty entry exists.

### Structure

```jsonc
{
  "employees": [             // List of all employees
    {
      "key": "int",          // Internal primary key ID
      "firstname": "string", // First name of the employee
      "name": "string",      // Last name of the employee
      "forbidden_days": [    // Days that are crossed off within TimeOffice = not available
        ["int"]
      ],
      "reserved": [          // Shifts that are crossed off within TimeOffice and worked in
        ["int", "string"]    // another PE = not available
      ],
      "vacation_days": [     // Days that are marked as vacation days = not available
        ["int"]
      ]
    }
  ]
}
```

---

# File: `general_settings.json`

### Description

This file contains qualifications of specific employees identified by their key.
The only qualification currently in use is "rounds".

### Structure

```jsonc
{
  "qualifications": {
    "employee_key_A": "list"["str"],
    "employee_key_B": "list"["str"],
    ...
  }
}
```

---

# File: `minimal_number_of_staff.json`

### Description

This file contains three tables in JSON Format: ["Azubi"](../user-view/list-of-conditions.md#azubis), [”Hilfskraft"](../user-view/list-of-conditions.md#hilfskräfte), ["Fachkräfte"](../user-view/list-of-conditions.md#fachkräfte). Those tables set the required number of employees of a specific type on every weekday for each shifts.

### Structure

```jsonc
{
  "Azubi": {
    "Mo": {
      "F": "int",
      "N": "int",
      "S": "int"
    },
    ...
  },
  "Hilfkraft": {
    "Mo": {
      "F": "int",
      "N": "int",
      "S": "int"
    },
    ...
  },
  "Fachkraft": {
    "Mo": {
      "F": "int",
      "N": "int",
      "S": "int"
    },
    ...
  }
}
```

---

# File: `shift_information.json`

### Description

This file contains all information known about each type of shift.

### Structure

```jsonc
  {
    "break_duration": "float",              // Break duration in Minutes
    "end_time": "string YYYY-MM-DDTHH:MM:SS",   // end of shift, timestamp
    "shift_duration": "float",              // difference between end and start in minutes
    "shift_id": "string",
    "shift_name": "string",
    "start_time": "string YYYY-MM-DDTHH:MM:SS",   // start of shift, timestamp
    "working_minutes": "float"              // shift duration minus break duration
  },
```

---

# File: `target_working_minutes.json`

### Description

This file contains the list of all employees within our PE (Planungseinheit) referring to their monthly target working minutes and the already existing working minutes within TimeOffice.

### Structure

```jsonc
{
  "employees": [             // List of all employees
    {
      "key": "int",          // Internal primary key ID
      "firstname": "string", // First name of the employee
      "name": "string",      // Last name of the employee
      "actual": "float",     // Already worked/registered working minutes within TimeOffice
      "target": "float"      // Target working minutes for the current month
    }
  ]
}
```

---

# File: `wishes_and_blocked.json`

### Description

This file contains the list of employees within our PE (Planungseinheit) which have submitted wishes of their preferences for off-shifts and off-days as well as unavailability due to special circumstances such as health or family-related restrictions. This file need to be created by hand as the wishes currently cannot be inserted via TimeOffice.

### Structure

```jsonc
{
  "employees": [               // List of all employees
    {
      "key": "int",            // Internal primary key ID
      "firstname": "string",   // First name of the employee
      "name": "string",        // Last name of the employee
      "blocked_days": ["int"], // Unavailable days due to health reasons, family-related restrictions or personal unavailability
      "blocked_shifts": [      // Unavailable shifts due to health reasons, family-related
        ["int", "string"]      // restrictions or personal unavailability
      ],
      "wish_days": ["int"],    // Days that employee wishes to get off or avoid
      "wish_shifts": [         // Shifts that employee wishes to get off or avoid
        ["int", "string"]
      ]
    }
  ]
}
```

# File: `worked_sundays.json`

### Description

This file contains the list of all employees within our PE (Planungseinheit) and how many sundays they have already worked in the last 12 months.

### Structure

```jsonc
{
  "employees": [               // List of all employees
    {
      "key": "int",            // Internal primary key ID
      "firstname": "string",   // First name of the employee
      "name": "string",        // Last name of the employee
      "worked_sundays": "int"  // Count of already worked sundays in last 12 months
    }
  ]
}
```
