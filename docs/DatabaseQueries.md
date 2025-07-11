# Database Queries
Overview of the Queries used to retrieve the needed personal data from the database and explanation.

## planning data

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

## shift_information.json

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

## target_working_minutes.json

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
