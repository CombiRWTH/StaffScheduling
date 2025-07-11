# Case Catalog
This is the file where all the different cases can be explained in more detail.

## Case 1:
- number of employees: 22
- to be continued...

## Case 2:
- number of employees: 371
- ...

## Case 3: - Real Data
In this case, the automatically extracted data from the database is stored. The `wishes_and_blocked.json` file is an exception because it includes all the manually submitted wishes of employees, as well as special circumstances, such as health- or family-related restrictions. The different files and their corresponding descriptions are listed below.

## 📁 File: `employees.json`

### 📝 Description

This file contains a list of all employees within our planning unit (Planungseinheit), including their `key` (internal ID), `personnel_number`, `name`, `firstname`, and `title` (job title).

### 📐 Structure

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

## 📁 File: `free_shifts_and_vacation_days.json`

### 📝 Description

This file contains the list of all employees within our PE (Planungseinheit) which already have submitted vacation days or shifts within TimeOffice or days that are either crossed off or worked within another PE. If an employee is not working somewehere else or has blocked days then an empty entry exists.

### 📐 Structure

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

## 📁 File: `target_working_minutes.json`

### 📝 Description

This file contains the list of all employees within our PE (Planungseinheit) referring to their monthly target working minutes and the already existing working minutes within TimeOffice.

### 📐 Structure

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

## 📁 File: `wishes_and_blocked.json`

### 📝 Description

This file contains the list of employees within our PE (Planungseinheit) which have submitted wishes of their preferences for off-shifts and off-days as well as unavailability due to special circumstances such as health or family-related restrictions. This file need to be created by hand as the wishes currently cannot be inserted via TimeOffice.

### 📐 Structure

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

## 📁 File: `worked_sundays.json`

### 📝 Description

This file contains the list of all employees within our PE (Planungseinheit) and how many sundays they have already worked in the last 12 months.

### 📐 Structure

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
