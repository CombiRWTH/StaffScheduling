# VM Process Documentation



## Accessing the VM

Download the required VM access files from Moodle, including:
- The `.rdp` file to connect to the VM
- The VM password

Use the `.rdp` file to establish a Remote Desktop connection and log in with the provided credentials.

---

## Environment Setup

Once connected to the VM:

- Open **TimeOffice**
- Log in using the credentials also found in Moodle
- Open the menu in the top-left and click on *Pläne öffnen*
- Double click a month to open the planning interface
- Save the initial plan to populate databases with staff info
- Click the dropdown next to the magic wand and select *rwth_staff_scheduling*
- This will execute a script found at `C:\Tools\run.bat` (or in the repo at `src/run.bat`) and launch the [workflow frontend](./web-interface.md) for the selected month and station.
- The relevant repositories are located in:

```
C:/Users/rwthadmin/Documents/
├── Staff Scheduling
└── Staff Scheduling Web
```
