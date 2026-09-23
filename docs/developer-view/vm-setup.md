# VM Setup

This page documents how to access and use the **project VM** deployed at St. Marien-Hospital Düren. The VM is the production environment where the solver is connected to the live TimeOffice database and run by hospital staff.

!!! note "Who needs this?"
    This guide is for project maintainers and handover recipients. If you are developing locally or running offline cases, see [Getting Started (Dev)](./getting-started-dev.md) instead.

---

## Accessing the VM

Download the required VM access files from Moodle, including:

- The `.rdp` file to connect to the VM
- The VM password

Use the `.rdp` file to establish a **Remote Desktop** connection and log in with the provided credentials.

---

## Environment Setup

Once connected to the VM:

1. Open **TimeOffice**
2. Log in using the credentials also found in Moodle
3. Open the menu in the top-left and click on *Pläne öffnen*
4. Double-click a month to open the planning interface
5. Save the initial plan to populate the database with staff info
6. Click the dropdown next to the magic wand and select *rwth_staff_scheduling*

This executes a script at `C:\Tools\run.bat` (also available in the repository at `legacy/src/run.bat`) which:

- Starts the **Staff Scheduling API** backend
- Launches the **StaffSchedulingWeb** frontend
- Opens the solver interface in the browser for the selected month and station

---

## Repository Locations on the VM

The relevant repositories are located in:

```
C:/Users/rwthadmin/Documents/
├── Staff Scheduling        ← This repository (Python backend + solver)
└── Staff Scheduling Web    ← StaffSchedulingWeb (Next.js frontend)
```

Both should be kept up to date by pulling from GitHub when updates are released.

---

## Known Notes

- The VM uses **Windows** and connects to the hospital network to reach the TimeOffice SQL Server.
- The ODBC Driver 18 for SQL Server is pre-installed on the VM — no manual driver installation is needed.
- If the API fails to start, check the `.env` file in the `Staff Scheduling` folder for correct database credentials.
- The TimeOffice database credentials are stored separately in Moodle and should **never** be committed to the repository.
