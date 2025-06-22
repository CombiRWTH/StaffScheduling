# 📱 Database Connection

This guide explains how to set up the connection to the **TimeOffice Database** using Python, manage credentials with a belonging `.env` file, and installing required dependencies from `requirements.txt`.

---

## 📁 Current Project Structure for the Database

```
StaffScheduling/
└── database/
    ├── connection_setup.py
    ├── .env
    ├── .env.template
    └── requirements.txt
```

---

## ✅ Prerequisites

* Python 3.x
* A valid SQL Server ODBC driver (e.g., ODBC Driver 17 or 18)
* Database credentials
* `pyodbc`, `pandas`, `python-dotenv` installed (see below)

---

## 🔧 Step 1 – Install Dependencies

Install Python packages:

```bash
pip install -r requirements.txt
```

---

## 🔐 Step 2 – Create a `.env` File

In the root directory, create a copy of the `.env.template` file and rename it to `.env`. Then add your given database credentials:

```env
DB_SERVER=your.database.server
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```
 (If needed, please contact one of the DB Team members as we do not want to publish the credentials given by Pradtke within GitHub)

---

## 🔌 Step 3 – Database Connection Script (`connection_setup.py`)

Run the given connection file by the following command;

```bash
python database/connection_setup.py
```

If everything is configured correctly, this will print a sample from the `TPersonal` table within a newly created file.
(Eventually you need to use command **python3** instead.)

---

## 📌 Useful Links

* [ODBC Driver for SQL Server (Microsoft Docs)](https://learn.microsoft.com/sql/connect/odbc/)
* [pyodbc Documentation](https://github.com/mkleehammer/pyodbc)

---
