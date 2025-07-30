# --8<-- [start:only-json-files-note]
!!! note
    Currently, our application lacks a user-friendly interface for comfortably managing configurations. Instead, these settings are stored in JSON files, which requires manual editing to make any changes.
# --8<-- [end:only-json-files-note]

Welcome to the configuration overview of our project! This document aims to provide users with a clear understanding of the various settings available within our application.

Our application features two modes: the full version, which connects to a centralized database, and the light version, designed for use without database access. In the light version without database access you can adjust all configurations, in contrast to the full version
where many configurations are already defined through the database.

In this overview, we will differentiate between user-adjustable configurations that can be modified at any time and those specific to the light version.

Let’s explore the available configurations!


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

- **Planned Shifts:** Preplan fixed shifts, e.g. special shifts (Z60). Normally done in TimeOffice, but in light-version it can be changed [here](./planned-shifts)
