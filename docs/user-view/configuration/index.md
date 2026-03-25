# --8<-- [start:only-json-files-note]
!!! note
    Configuration can be managed in two ways:

    - Preferred: via the browser-based [StaffSchedulingWeb](https://julian466.github.io/StaffSchedulingWeb/) interface.
    - Advanced/manual: by editing the JSON files in the case folder directly.

    For month-based cases, files are usually located in `cases/{case_id}/{MM_YYYY}/...` (for example `cases/77/11_2024/...`).
# --8<-- [end:only-json-files-note]

This section explains which settings are available and where they are stored.

If you use StaffSchedulingWeb, you can maintain these settings through forms in the UI. The solver still reads the same JSON files in this repository.

In CLI/light workflows, you can edit these files manually.



## User-Adjustable Configurations


- **Forbidden Days and Shifts**: Configure specific days or shifts when certain employees are not allowed to work [here](./forbidden-days).

- **Rounds Permission**: Set up which employees need to be available for early weekday rounds (*german: Visiten*) [here](./rounds-permissions). Our application ensures at least one of these employees is assigned to an early shift.

- **Minimum Number of Staff**: Define the minimal number of staff required per type ("Hilfskraft", "Fachkraft" or "Azubi") for each day of the week and shift [here](./min-staff).

- **Qualification Mapping**: Assign each qualification label from the database to one of the three types: "Hilfskraft", "Fachkraft" or "Azubi" [here](./qualifications).

- **Weights**: Adjust the importance of objectives in the general objective function [here](./weights).

- **Blocked Shifts and Days:** Adjust availability of employees manually (!= vacation days) [here](./blocked-shifts), e.g. block all night shifts if the person is not allowed to work at night, or block each Thursday if the employee does not work on Thursdays.


## Light-Version Exclusives

- **Vacation Days**: Manually configure vacation days and free shifts, as they are normally set in TimeOffice and imported automatically [here](./vacation-days).

- **Employees**: Modify employee information that is typically managed in TimeOffice [here](./staff).

- **Planned Shifts:** Preplan fixed shifts, e.g. special shifts (Z60). Normally done in TimeOffice, but in light-version it can be changed [here](./planned-shifts).
