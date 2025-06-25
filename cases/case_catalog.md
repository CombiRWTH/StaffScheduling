# Case Catalog
This is the file where all the different cases can be explained in more detail.
Is this real data or dummy data? How many employees? And special constraints?

## Case 1:
- number of employees: 22
- to be continued...

## Case 2:
- number of employees: 371
- ...

## Case 3:
Within this case the automatically extracted data from the database is stored. This excludes the `wishes_and_blocked.json` file as this includes all the manually submitted wishes of employees as well as special circumstances such as health or family-related restrictions. All different files are listed below with the corresponding description of each field within them.

## 📁 File: `employees.json`

### 📝 Description

This file contains the list of all employees within our PE (Planungseinheit), including their internal ID, personnel number, name, and their job title.

### 📐 Structure

```jsonc
{
  "employees": [            // List of all employees
    {
      "PersNr": "string",   // Personnel number as a string
      "Prim": integer,      // Internal primary key ID
      "firstname": "string",// First name of the employee
      "name": "string",     // Last name of the employee
      "type": "string"      // Job title (may include an intern classification code)
    },
    ...
  ]
}
