# Database Queries
Overview of the queries used to retrieve the needed personal data from the database. All of these queries can be found within the `export_data.py`-file, each capsulated in a separate function for simplified expansion.

## Basic Plan Data

```sql
SELECT
	Prim AS 'plan_id',
	RefPlanungseinheiten AS 'planning_unit',
	VonDat AS 'from_date',
	BisDat AS 'till_date'
FROM TPlan
WHERE RefPlanungseinheiten = {planning_unit}
    AND VonDat = CONVERT(date,'{from_date}',23)
    AND BisDat = CONVERT(date,'{till_date}',23)
```

We use the entity `TPlan` to retrieve the `plan identification number` of a corresponding schedule. The ID is the numeric primay key `Prim` of the entity. It is unique by a given planning unit and a period of time.
`RefPlanungseinheiten` is the reference to the underlying planning unit and stored in `TPlanungseinheiten`.
To get a certain id `VonDat` needs to be the first day of a month and `BisDat` the last day of a month.
The `CONVERT`-function uses the style code "23" that specifies the date format `yyyy-mm-dd`.

## Export shift_information.json

```sql
SELECT
    RefDienste AS 'shift_id',
    Kommt AS 'start',
    Geht AS 'end'
FROM TDiensteSollzeiten
WHERE RefDienste = '{shift_ids["Frühschicht"]["id"]}'
    OR RefDienste = '{shift_ids["Spätschicht"]["id"]}'
    OR RefDienste = '{shift_ids["Nachtschicht"]["id"]}'
    OR RefDienste = '{shift_ids["Zwischendienst"]["id"]}'
    OR RefDienste = '{shift_ids["Sonderdienst"]["id"]}'
```

We use the entity `TDiensteSollzeiten` to retrieve the start and end times for specific work shifts. To collect the time information a defined set of shift types (Frühschicht, Spätschicht, Nachtschicht, Zwischendienst und Sonderdienst) is used.
The unique identifier for a shift is a reference in `TDiensteSollzeiten` and stored in `RefDienste` as an integer.
The entity contains the start `Kommt` and the end `Geht` of a shift, referenced by their shift ID. The date format is `yyyy-mm-dd hh-mi-ss`.
These values are further used to compute the shift duration, break duration and the total working minutes of a shift.

## Export employees.json

```sql
SELECT
    a.Prim,
    a.Name,
    a.Vorname,
    a.PersNr,
    t.Bezeichnung AS 'Beruf'
FROM TPlanPersonal b
JOIN TPersonal a ON b.RefPersonal = a.Prim
LEFT JOIN TBerufe t ON a.RefBerufe = t.Prim
WHERE RefPlan = {plan_id}
```
We use this query to retrieve detailed information about the personal staff. The following tables are involved:
- `TPersonal` (a): stores detailed employee information
- `TPlanPersonal` (b): links plannings entities
- `TBerufe` (t): contains short and long descriptions of occupations

The `Inner Join` ensures that only staff information with exisiting records are included. The `Left Join` is used to receive the job description for each employees, if available. Employees without a job reference will still appear, with `NULL` in the `Beruf` column.

For a specific `plan_id` we obtain the unique numeric primary key `Prim`, the surname `Name` and first name `Vorname`, the personnel number `PersNr` and the occupation `Bezeichnung` of all employees within the underlying work schedule.

## Export target_working_minutes.json

```sql
SELECT
	p.PersNr,
	p.Name AS 'name',
	p.Vorname AS 'firstname',
	pkt.RefKonten,
	pkt.Wert2
FROM TPersonalKontenJeMonat pkt
JOIN TPersonal p ON pkt.RefPersonal = p.Prim
WHERE (pkt.RefKonten = 1  OR pkt.RefKonten = 19 OR pkt.RefKonten = 55)
	AND pkt.Monat = '202411'
ORDER BY p.Name asc
```

We use the entity `TPersonalKontenJeMonat` to retrieve the working hours of each employee per month.
We join this entity with `TPersonal` to obtain the employee's `Name` and `PersNr`.
The `RefKonten` field in the `TPersonalKontenJeMonat` entity provides the relevant type of Konto (e.g., SOLL_Monat). All types of Konten can be found in the entity `TKonten`.

In our case these are:
1. "1" := SOLL_Monat (first Column in TimeOffice)
2. "19" := Arbeitsstunden
3. "55" := Total

The tricky thing here is that the different Konten are only created when needed.
For example, if an employee has not yet been scheduled in the plan, only a "1" Konto is present in the entity `TPersonalKontenJeMonat`.
The same applies to the "19" and "55" Konten.
Some employees only have a "19" Arbeitsstunden Konto, which represents the "Arbeitsstunden / IST Stunden" respectively.
Other employees have both a "19" and a "55" Konto.
In that case the "55" Konto represents the correct "IST Stunden" ("19" = "55" or "19" < "55").

Once we have identified the correct values using the entity `RefKonten`, we can obtain the hours from `Wert2`.
Since we are using working minutes and not hours, we must multiply by 60 to get the correct number of working minutes.

## Export worked_sundays.json

```sql
SELECT
    p.Prim,
    p.Name AS name,
    p.Vorname AS firstname,
    COUNT(DISTINCT CAST(pkt.Datum AS DATE)) AS worked_sundays
FROM TPersonalKontenJeTag pkt
JOIN TPersonal p ON pkt.RefPersonal = p.Prim
WHERE pkt.RefKonten = 40
    AND pkt.Datum BETWEEN {from_date} AND {till_date}
    AND DATENAME(WEEKDAY, pkt.Datum) = 'Sonntag'
    AND pkt.Wert > 0
GROUP BY
    p.Prim,
    p.Name,
    p.Vorname
ORDER BY
    worked_sundays DESC
```

We use the `TPersonalKontenjeTag` table to retrieve the number of worked sunday shifts for each employee for the last 12 months. The table stores daily entries and account types per employee. The `Inner Join` links this table with `TPersonal` to receive the employees' unique primary key `Prim`, as well as the surname `Name` and the first name `Vorname`. In the following the conditions are described:
- `pkt.RefKonten = 40`:  "40" is the account key for a sunday shift
- `pkt.Datum BETWEEN {from_date} AND {till_date}`: defines the date range, in our case, of 12 months
- `DATENAME(WEEKDAY, pkt.Datum) = 'Sonntag'`: filters the weekday, for this query it is `sunday`
- `pkt.Wert > 0`: includes only days with positive values, means actual work days

Lastly we aggregate the worked days per employee with `GROUP` and rank them by the number of worked shifts on a sunday with `ORDER BY`.

## Get plan dates

```sql
SELECT
CAST(VonDat AS DATE) AS 'START',
CAST(BisDat AS DATE) AS 'END'
FROM TPlan WHERE Prim = '{plan_id}'
```

We use the `TPlan` table to get the start and the end dates of a specific plan defined by the given plan ID `plan_id`. The date format is `yyyy-mm-dd`.

## Export free_shifts_and_vacation_days.json

### Query for vacation days

```sql
SELECT
    p.Prim AS Prim,
    p.Name AS name,
    p.Vorname AS firstname,
    pkg.Datum AS vacation_days
FROM TPlanPersonalKommtGeht pkg
JOIN TPersonal p ON pkg.RefPersonal = p.Prim
WHERE pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23)
    AND CONVERT(date,'{END_DATE}',23)
    AND pkg.RefgAbw IN (20, 2434, 2435, 2091)
```

This SQL query retrieves a list of employees and the dates they took (additional) vacation days within a specified date range. To get these information we use the `TPlanPersonalKommtGeht` table which stores the attendance and absence records, including absence types, for each employee. To obtain the surname `Name` and the first name `Vorname` we use the `Inner Join` with the `TPersonal` table. The last column `vacation_days` stores the days when the vacation will take place.
In the `WHERE` section, we first filter the records in the desired date period. The `CONVERT`-function again uses the style code "23" that specifies the date format `yyyy-mm-dd`. In addition, we filter the `RefgAbw` for specific vacation types: "20", "2434", "2435" represent a standard vacation day `Urlaub`, "2091" represents an additional vacation day `Zusatzurlaub`. Full-day absence are stored in `RefgAbw`.

### Query for forbidden days

```sql
SELECT
    p.Prim AS Prim,
    p.Name AS 'name',
    p.Vorname AS 'firstname',
    pkg.Datum AS 'forbidden_days'
FROM TPlanPersonalKommtGeht pkg
JOIN TPersonal p ON pkg.RefPersonal = p.Prim
WHERE pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23)
AND CONVERT(date,'{END_DATE}',23)
AND pkg.RefgAbw NOT IN (20, 2434, 2435, 2091)
```

This query is very similar to the `vacation query`. To get the information we again use the `TPlanPersonalKommtGeht` table and obtain the surname `Name` and the first name `Vorname` with the `Inner Join` with the `TPersonal` table.
The difference is that for each employee, we want to retrieve the full-day absences from `RefgAbw` that are not vacation days. Therefore, the last column `forbidden_days` stores the days on which an employee is not be selected for a shift for reasons other than vacation. Other reasons could be, for example:
- parental leave (absence type "1078")
- pension (absence type "1086")
- day off (absence type "1089")

The distinction is necessary here because a vacation day has an impact on an employee's target working hours, while a day off, for example, has no impact.

### Query for forbidden shifts

```sql
SELECT
    p.Prim AS Prim,
    p.Name AS 'name',
    p.Vorname AS 'firstname',
    pkg.Datum AS 'planned_shifts',
    d.KurzBez AS 'dienst'
FROM TPlanPersonalKommtGeht pkg
JOIN TPersonal p ON pkg.RefPersonal = p.Prim
JOIN TDienste d ON pkg.RefDienste = d.Prim
WHERE pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23)
AND CONVERT(date,'{END_DATE}',23)
AND pkg.RefgAbw IS NULL
```

This query retrieves the already planned work shifts for other planning units for employees within a given time period. This means that an employee working in another planning unit is unavailable for our schedule.
To do this, we again use `TPlanPersonalKommtGeht` and `TPersonal` for the same information, as well as `TDienste` to identify the already planned shift.
To obtain the desired records, i.e., the actual scheduled shifts, we exclude all absence records, with `RefgAbw` set to `NULL`. This means that the employees are already scheduled to work.

### Query for accounting entries

```sql
SELECT
    RefPersonal AS Prim,
    Datum
FROM  TPersonalKontenJeTag
WHERE RefPlanungsEinheiten = {planning_unit}
AND Datum BETWEEN CONVERT(date,'{START_DATE}',23)
AND CONVERT(date,'{END_DATE}',23)
```

We use `TPersonalKontenJeTag` to retrieve the present days of the employees of a desired planning unit. The `CONVERT`-function again uses the style code "23" that specifies the date format `yyyy-mm-dd`.
