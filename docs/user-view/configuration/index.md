This chapter aims to give users a clear understanding of the various configuration options available in our application.

The application has two modes: a fully integrated version that connects to a centralized database and a light version designed for use without database access.
With the light version, you can adjust all configurations.
In contrast, many configurations are already defined through the database in the full version.

This overview will explain the difference between configurations that can be modified at any time by the user and configurations specific to the light version.

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
