# File Overview

This guide explains how to set up the connection to the **TimeOffice Database** using Python and credentials in the belonging `.env`-file.

---

### Current Project Structure for the Database

```
StaffScheduling/
├──  src/
    └── db/
        ├── connection_setup.py  # Establishes a connection to the TimeOffice Database
        ├── export_data.py       # Includes separate functions retrieving data for our algorithm
        ├── export_main.py       # Collects all function calls from 'export_data.py' with an established connection
        ├── import_main.py       # Collects all function calls from 'import_data.py' with an established connection
        └── import_solution.py   # Includes separate functions importing solution data from our algorithm

├── .env                         # Holds credentials for the database connection
└── .env.template                # Template to put in given credentials
```

---

# Database Connection

## Prerequisites

* Python 3.x
* A valid SQL Server ODBC driver [(ODBC Driver for SQL Server (Microsoft Docs))](https://learn.microsoft.com/sql/connect/odbc/)
* TimeOffice Database credentials
* `pyodbc` and `pandas` packages installed

These should be installed already when following the `Getting-Started (Dev)`-Guide from our documentation. Otherwise check for each required prerequisite if it is installed within your local environment and install separately if needed.

---

### Create a `.env`-File

In the root directory, create a copy of the `.env.template` file and rename it to `.env`. Then add your given database credentials:

```env
DB_SERVER=your.database.server
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```
 (If needed, please contact one of the **DB-Team**-members as we do not want to publish the credentials given by Pradtke within GitHub or directly contact **Pradtke**)

---

### Following the Process Flow

From now on you can follow on with the commands within the `Getting-Started (Dev)`-Guide or refer to the other database documentation files for further understanding.

---
