# Database Queries
This is an overview of the queries used to retrieve the necessary personal data from the database, along with an explanation.

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
WHERE (pkt.RefKonten = 1  OR pkt.RefKonten = 19 OR pkt.RefKonten = 55) AND pkt.Monat = '202411'
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
