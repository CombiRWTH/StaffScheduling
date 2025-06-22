# Database Queries
Overview of the Queries used to retrieve the needed personal data from the database and explanation.

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

We use the **TPersonalKontenJeMonat** table to retrieve the working hours of each employee per month.
We JOIN that table with **TPersonal** to directly get the corresponding names and PersNr of the employee.
RefKonten in TPersonalKontenJeMonat gives us the relevant type of Konto (f.e. SOLL_Monat). You can find all types of Konten in **TKonten**.

In our case these are:
1. "1" := SOLL_Monat (first Column in TimeOffice)
2. "19" := Arbeitsstunden
3. "55" := Total

The tricky thing here is that the different Konten are only "created" when they are needed, i. e. if an employee is not yet scheduled in the plan,
there is only a "1" Konto in the TPersonalKontenJeMonat. The same thing applies to the "19" and "55" Konten, some employees only have a "19" Arbeitsstunden Konto,
which represents the "Arbeitsstunden / IST Stunden" respectively. Other employees have a "19" as well as a "55" Konto, in that case the "55" Konto represents the right "IST Stunden" ("19" = "55" or "19" < "55").

Once we have identified the right values using "RefKonten", we can get the hours from **Wert2**. As we use the working minutes and not hours, we finally have to multiply by 60 to get the right amount of working minutes.
