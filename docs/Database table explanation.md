# Database table explanation

## TPlan:
TPlan describes the set of working schedule managed in TIMEOFFICE. A working schedule is always assigned to a planning unit (Planungseinheit) and a time period. The time period is determined by the planning interval of the underlying planning unit.

| Attribute    | Description |
| -------- | ------- |
| Prim  | Unique numeric primary key    |
| RefPlanungseinheiten | Reference to the underlying planning unit, TPlanungseinheiten.Prim |
| VonDat    | Start time of planning    |
| BisDat    | End time of planning   |
| RefStati    | The status in which the work schedule is located. Reference to STStati (sic!) The most relevant statuses are 20 (TARGET), 50 (ACTUAL) and 70 (COMPLETED) or 80 (OVERDUE). Schedules in status 20 are in target planning, i.e. are currently still being planned prospectively. Plans with status 50 are in the actual planning stage; as a rule, failures are documented here and rescheduling is carried out. Plans with status 70 have been committed and can no longer be changed; status 80 indicates that a plan with status 70 has already been settled.    |
| RefPlanungsIntervalle    | The planning interval of the plan. Reference to STPlanungsIntervalle (de facto only relevant: 1 = monthly planning, 3 = annual planning) See also TPlanungseinheiten.RefPlanungsintervalle. Special: A planning unit can (and often will) have both plans with status 1 AND 3. Planning interval 3 is then the annual plan, in which long-term absence planning usually takes place. The actual work schedule then have interval 1.    |


## TPlanPersonal:
TPlanPersonal describes the assignment of an employee to a specific work schedule.

| Attribute    | Description |
| -------- | ------- |
| Prim  | Unique numeric primary key    |
| RefPlan  | Reference to the underlying work schedule, TPlan.Prim    |
| RefPersonal  | Reference to the underlying employee, TPersonal.Prim    |
| RefBerufe  | Occupation of the employee on the plan, TBerufe.Prim    |
| VonDat  | Start of the employee's assignment, always within the plan limits    |
| BisDat  | End of the employee's assignment, always within the plan limits    |
| IstVonErsatz  | Indicator as to whether it is a substitute assignment    |


## TPersonal:
TPersonal describes the master data of an individual employee.
#### This table contains many fields that are now obsolete.

| Attribute    | Description |
| -------- | ------- |
| Prim  | Unique numeric primary key    |
| PersNr  | Personnel number of the employee    |
| Name  | Surname of the employee    |
| Vorname  | First name of the employee    |
| GebDat  | Date of birth of the employee    |
| EinDat  | Date on which the employee joined the company. Hiring date    |
| AusDat  | Date on which the employee leaves the company. Dismissal date    |
| RefGeschlechter  | Reference to STGeschlechter. 1 male, 2 female, 3 diverse.    |
| RefFamilienstand  | Marital status of the employee. Reference to TKataloge, RefKatalogArt 1    |
| RefBerufe  | The training occupation of the employee. Reference to TBerufe.    |
| RefEinrichtungen  | The institution to which this employee is assigned.    |



