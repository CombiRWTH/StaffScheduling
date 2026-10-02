-- Read-only readiness of stations 77, 79 and jumper pool 408 for every month 2026-01 to 2026-06, following the
-- adapter's checklist for supporting another unit: target plans, memberships with mapped professions and one home
-- per date, names, valid targets, mapped absences with their credits, saved demand and context plans. Every row
-- carries `ok` = 1 when met. The last two statements report daily headcount and hours against demand.
-- The adapter's mappings and the NRW holidays come from temporary tables that the test fills from facts.py and the
-- calendar: #profession_level(code, lvl), #absence_code(code), #credited_absence(account, code), #holiday(d).

-- 1 + 2 Units and exactly one status-20 monthly full-month target plan per station and month
WITH months AS (
    SELECT CAST('20260101' AS date) AS m UNION ALL SELECT DATEADD(month, 1, m) FROM months WHERE m < '20260601')
SELECT u.Prim AS unit, mo.m AS month, u.RefPlanungsIntervalle AS interval_,
    (SELECT COUNT(*) FROM TPlan p WHERE p.RefPlanungseinheiten = u.Prim AND p.RefStati = 20
        AND p.RefPlanungsIntervalle = 1 AND CONVERT(date, p.VonDat) = mo.m AND CONVERT(date, p.BisDat) = EOMONTH(mo.m)) AS target_plans,
    CASE WHEN u.RefPlanungsIntervalle = 1 AND (SELECT COUNT(*) FROM TPlan p WHERE p.RefPlanungseinheiten = u.Prim
        AND p.RefStati = 20 AND p.RefPlanungsIntervalle = 1 AND CONVERT(date, p.VonDat) = mo.m
        AND CONVERT(date, p.BisDat) = EOMONTH(mo.m)) = 1 THEN 1 ELSE 0 END AS ok
FROM TPlanungseinheiten u CROSS JOIN months mo WHERE u.Prim IN (77, 79)
ORDER BY unit, month
GO
-- 3 + 4 + 5 Per month: members, unmapped professions (membership or employee), missing names, missing/invalid targets
WITH months AS (
    SELECT CAST('20260101' AS date) AS m UNION ALL SELECT DATEADD(month, 1, m) FROM months WHERE m < '20260601'),
mapped(code, lvl) AS (SELECT code, lvl FROM #profession_level),
scope AS (
    SELECT mo.m, pep.RefPersonal, pep.RefBerufe FROM months mo JOIN TPlanungseinheitenPersonal pep
        ON pep.RefPlanungseinheiten IN (77, 79, 408) AND ISNULL(pep.KeinEPlan, 0) = 0
        AND CONVERT(date, pep.VonDat) <= EOMONTH(mo.m) AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= mo.m)),
flags AS (
    SELECT s.m, s.RefPersonal,
        CASE WHEN mm.code IS NULL THEN 1 ELSE 0 END AS bad_membership,
        CASE WHEN mp.code IS NULL THEN 1 ELSE 0 END AS bad_employee,
        CASE WHEN LTRIM(RTRIM(ISNULL(per.Name, ''))) + LTRIM(RTRIM(ISNULL(per.Vorname, ''))) = '' THEN 1 ELSE 0 END AS unnamed,
        CASE WHEN a.Wert2 IS NULL OR a.Wert2 < 0 THEN 1 ELSE 0 END AS no_target
    FROM scope s JOIN TPersonal per ON per.Prim = s.RefPersonal
    LEFT JOIN TBerufe bm ON bm.Prim = s.RefBerufe LEFT JOIN TBerufe bp ON bp.Prim = per.RefBerufe
    LEFT JOIN mapped mm ON mm.code = LTRIM(RTRIM(bm.KurzBez)) LEFT JOIN mapped mp ON mp.code = LTRIM(RTRIM(bp.KurzBez))
    LEFT JOIN TPersonalKontenJeMonat a ON a.RefPersonal = s.RefPersonal AND a.RefKonten = 1
        AND a.Monat = YEAR(s.m) * 100 + MONTH(s.m))
SELECT m AS month, COUNT(DISTINCT RefPersonal) AS employees, SUM(bad_membership) AS unmapped_memberships,
    COUNT(DISTINCT CASE WHEN bad_employee = 1 THEN RefPersonal END) AS unmapped_employees,
    COUNT(DISTINCT CASE WHEN unnamed = 1 THEN RefPersonal END) AS unnamed,
    COUNT(DISTINCT CASE WHEN no_target = 1 THEN RefPersonal END) AS missing_targets,
    CASE WHEN SUM(bad_membership) + SUM(bad_employee) + SUM(unnamed) + SUM(no_target) = 0 THEN 1 ELSE 0 END AS ok
FROM flags GROUP BY m ORDER BY m
GO
-- 3 One home per employee and active date (among configured units)
WITH days AS (
    SELECT CAST('20260101' AS date) AS d UNION ALL SELECT DATEADD(day, 1, d) FROM days WHERE d < '20260630'),
active AS (
    SELECT dy.d, pep.RefPersonal, pep.IstHeimat, pep.RefPlanungseinheiten FROM days dy JOIN TPlanungseinheitenPersonal pep
        ON pep.RefPlanungseinheiten IN (77, 79, 408) AND ISNULL(pep.KeinEPlan, 0) = 0
        AND CONVERT(date, pep.VonDat) <= dy.d AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= dy.d)),
homes AS (
    SELECT d, RefPersonal, COUNT(DISTINCT CASE WHEN IstHeimat = 1 THEN RefPlanungseinheiten END) AS n FROM active GROUP BY d, RefPersonal)
SELECT FORMAT(d, 'yyyy-MM') AS month, COUNT(*) AS employee_days, SUM(CASE WHEN n <> 1 THEN 1 ELSE 0 END) AS without_one_home,
    CASE WHEN SUM(CASE WHEN n <> 1 THEN 1 ELSE 0 END) = 0 THEN 1 ELSE 0 END AS ok
FROM homes GROUP BY FORMAT(d, 'yyyy-MM') ORDER BY month
OPTION (MAXRECURSION 400)
GO
-- 3 Jumper pool: every 408 member has a planned Ersatz membership at each station covering the month
WITH months AS (
    SELECT CAST('20260101' AS date) AS m UNION ALL SELECT DATEADD(month, 1, m) FROM months WHERE m < '20260601'),
covered AS (
    SELECT mo.m, h.RefPersonal, COUNT(DISTINCT e.RefPlanungseinheiten) AS stations
    FROM months mo JOIN TPlanungseinheitenPersonal h ON h.RefPlanungseinheiten = 408 AND h.IstHeimat = 1
        AND CONVERT(date, h.VonDat) <= EOMONTH(mo.m) AND (h.BisDat IS NULL OR CONVERT(date, h.BisDat) >= mo.m)
    LEFT JOIN TPlanungseinheitenPersonal e ON e.RefPersonal = h.RefPersonal AND e.RefPlanungseinheiten IN (77, 79)
        AND e.IstVonErsatz = 1 AND ISNULL(e.KeinEPlan, 0) = 0 AND CONVERT(date, e.VonDat) <= mo.m
        AND (e.BisDat IS NULL OR CONVERT(date, e.BisDat) >= EOMONTH(mo.m))
    GROUP BY mo.m, h.RefPersonal)
SELECT m AS month, COUNT(*) AS jumper_pool_members, SUM(CASE WHEN stations = 2 THEN 1 ELSE 0 END) AS with_ersatz,
    CASE WHEN SUM(CASE WHEN stations = 2 THEN 1 ELSE 0 END) = COUNT(*) THEN 1 ELSE 0 END AS ok
FROM covered GROUP BY m ORDER BY m
GO
-- 6 Absence codes (mapped or ignored), unbooked credited Mon-Fri non-holiday absences, orphan credits; in scope, Jan-Jun
WITH emps AS (
    SELECT DISTINCT RefPersonal FROM TPlanungseinheitenPersonal pep WHERE pep.RefPlanungseinheiten IN (77, 79, 408)
        AND ISNULL(pep.KeinEPlan, 0) = 0 AND CONVERT(date, pep.VonDat) <= '20260630' AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= '20260101')),
known(code) AS (SELECT code FROM #absence_code),
credit_code(account, code) AS (SELECT account, code FROM #credited_absence),
holidays(d) AS (SELECT d FROM #holiday),
absences AS (
    SELECT k.RefPersonal, CONVERT(date, k.Datum) AS d, LTRIM(RTRIM(COALESCE(ga.KurzBez, da.KurzBez))) AS code
    FROM TPlanPersonalKommtGeht k LEFT JOIN TDienste ga ON ga.Prim = k.RefgAbw LEFT JOIN TDienste da ON da.Prim = k.RefDienstAbw
    WHERE k.RefPersonal IN (SELECT RefPersonal FROM emps) AND CONVERT(date, k.Datum) BETWEEN '20260101' AND '20260630'
        AND ISNULL(k.Wunschdienst, 0) = 0 AND (k.RefgAbw IS NOT NULL OR k.RefDienstAbw IS NOT NULL)),
credits AS (
    SELECT t.RefPersonal, CONVERT(date, t.Datum) AS d, c.code
    FROM TPersonalKontenJeTag t JOIN credit_code c ON c.account = t.RefKonten
    WHERE t.RefPersonal IN (SELECT RefPersonal FROM emps) AND CONVERT(date, t.Datum) BETWEEN '20260101' AND '20260630'),
problems AS (
    SELECT d, 'unmapped absence code ' + ISNULL(code, 'NULL') AS what FROM absences WHERE code IS NULL OR code NOT IN (SELECT code FROM known)
    UNION ALL
    SELECT a.d, 'credited absence without credit' FROM absences a
        WHERE a.code IN (SELECT code FROM credit_code) AND DATEDIFF(day, '19000101', a.d) % 7 < 5 AND a.d NOT IN (SELECT d FROM holidays)
        AND NOT EXISTS (SELECT 1 FROM credits c WHERE c.RefPersonal = a.RefPersonal AND c.d = a.d AND c.code = a.code)
    UNION ALL
    SELECT c.d, 'credit without absence' FROM credits c
        WHERE NOT EXISTS (SELECT 1 FROM absences a WHERE a.RefPersonal = c.RefPersonal AND a.d = c.d AND a.code = c.code))
SELECT (SELECT COUNT(*) FROM absences) AS absences, (SELECT COUNT(*) FROM credits) AS credits,
    (SELECT COUNT(*) FROM problems) AS problems,
    (SELECT STRING_AGG(CONCAT(FORMAT(d, 'yyyy-MM-dd'), ' ', what), '; ') FROM (SELECT TOP 20 d, what FROM problems ORDER BY d) p) AS first_problems,
    CASE WHEN (SELECT COUNT(*) FROM problems) = 0 THEN 1 ELSE 0 END AS ok
GO
-- 7 Saved demand per station month
WITH months AS (
    SELECT CAST('20260101' AS date) AS m UNION ALL SELECT DATEADD(month, 1, m) FROM months WHERE m < '20260601')
SELECT u.unit, mo.m AS month,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingDemandMonth dm WHERE dm.planning_unit_id = u.unit AND dm.planning_month = mo.m) AS saved,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingDemand d WHERE d.planning_unit_id = u.unit AND d.demand_date BETWEEN mo.m AND EOMONTH(mo.m)) AS rows_,
    CASE WHEN (SELECT COUNT(*) FROM dbo.StaffSchedulingDemandMonth dm WHERE dm.planning_unit_id = u.unit AND dm.planning_month = mo.m) = 1
        THEN 1 ELSE 0 END AS ok
FROM (VALUES (77), (79)) u(unit) CROSS JOIN months mo ORDER BY u.unit, mo.m
GO
-- Context: the dates the adapter reads around the months (5 before, 3 after: 2025-12-27..31, 2026-07-01..03) lie in a
-- status-30 plan of every station (05-context-plans.sql creates 2025-12-18..31 and 2026-07-01..07), with no duty inside Jan-Jun
WITH days AS (
    SELECT CAST('20251227' AS date) AS d UNION ALL SELECT DATEADD(day, 1, d) FROM days WHERE d < '20260703'),
covered AS (
    SELECT u.unit, dy.d, CASE WHEN EXISTS (SELECT 1 FROM TPlan p WHERE p.RefPlanungseinheiten = u.unit AND p.RefStati = 30
        AND CONVERT(date, p.VonDat) <= dy.d AND CONVERT(date, p.BisDat) >= dy.d) THEN 1 ELSE 0 END AS c
    FROM (VALUES (77), (79)) u(unit) CROSS JOIN days dy WHERE dy.d < '20260101' OR dy.d > '20260630'),
inside AS (
    SELECT p.RefPlanungseinheiten AS unit, COUNT(k.RefPlan) AS n FROM TPlan p
    LEFT JOIN TPlanPersonalKommtGeht k ON k.RefPlan = p.Prim AND CONVERT(date, k.Datum) BETWEEN '20260101' AND '20260630'
    WHERE p.RefPlanungseinheiten IN (77, 79) AND p.RefStati = 30 GROUP BY p.RefPlanungseinheiten)
SELECT c.unit, SUM(c.c) AS covered_days, MAX(ISNULL(i.n, 0)) AS duties_inside,
    CASE WHEN SUM(c.c) = 8 AND MAX(ISNULL(i.n, 0)) = 0 THEN 1 ELSE 0 END AS ok
FROM covered c LEFT JOIN inside i ON i.unit = c.unit GROUP BY c.unit
OPTION (MAXRECURSION 400)
GO
-- Informational: daily headcount. Per month and level, the days on which the people able to work that date (home
-- staff of both stations plus the jumper pool, without a blocking roster absence or project availability) are fewer
-- than the day's demand slots of both stations. One person fills at most one slot a day, so each such day has an
-- unavoidable gap of at least the shortfall. Stations are combined because the jumper pool serves both in one run.
WITH days AS (
    SELECT CAST('20260101' AS date) AS d UNION ALL SELECT DATEADD(day, 1, d) FROM days WHERE d < '20260630'),
mapped(code, lvl) AS (SELECT code, lvl FROM #profession_level),
need AS (
    SELECT d.demand_date AS d, d.staff_level AS lvl, SUM(d.required_count) AS slots FROM dbo.StaffSchedulingDemand d
    WHERE d.planning_unit_id IN (77, 79) AND d.demand_date BETWEEN '20260101' AND '20260630' GROUP BY d.demand_date, d.staff_level),
people AS (
    SELECT dy.d, mm.lvl, COUNT(DISTINCT pep.RefPersonal) AS heads
    FROM days dy JOIN TPlanungseinheitenPersonal pep ON pep.RefPlanungseinheiten IN (77, 79, 408) AND pep.IstHeimat = 1
        AND ISNULL(pep.KeinEPlan, 0) = 0 AND CONVERT(date, pep.VonDat) <= dy.d AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= dy.d)
    JOIN TBerufe b ON b.Prim = pep.RefBerufe JOIN mapped mm ON mm.code = LTRIM(RTRIM(b.KurzBez))
    WHERE NOT EXISTS (SELECT 1 FROM TPlanPersonalKommtGeht k LEFT JOIN TDienste ga ON ga.Prim = k.RefgAbw
            LEFT JOIN TDienste da ON da.Prim = k.RefDienstAbw
            WHERE k.RefPersonal = pep.RefPersonal AND CONVERT(date, k.Datum) = dy.d AND ISNULL(k.Wunschdienst, 0) = 0
                AND (k.RefgAbw IS NOT NULL OR k.RefDienstAbw IS NOT NULL)
                AND LTRIM(RTRIM(COALESCE(ga.KurzBez, da.KurzBez))) NOT IN ('FR'))
        AND NOT EXISTS (SELECT 1 FROM dbo.StaffSchedulingAvailability a WHERE a.employee_id = pep.RefPersonal
            AND a.availability_date = dy.d AND a.availability_type IN (N'unavailable', N'vacation', N'training', N'free_day'))
    GROUP BY dy.d, mm.lvl)
SELECT FORMAT(n.d, 'yyyy-MM') AS month, n.lvl AS level, MAX(n.slots) AS max_daily_slots, MIN(ISNULL(p.heads, 0)) AS min_daily_heads,
    SUM(CASE WHEN ISNULL(p.heads, 0) < n.slots THEN 1 ELSE 0 END) AS short_days,
    SUM(CASE WHEN ISNULL(p.heads, 0) < n.slots THEN n.slots - ISNULL(p.heads, 0) ELSE 0 END) AS unavoidable_gap_slots
FROM need n LEFT JOIN people p ON p.d = n.d AND p.lvl = n.lvl
GROUP BY FORMAT(n.d, 'yyyy-MM'), n.lvl ORDER BY month, level
OPTION (MAXRECURSION 400)
GO
-- Informational: demand hours vs. available hours (targets minus credits) per station month and level, home staff,
-- with the jumper pool listed as its own unit. Paid hours per shift come from TDiensteSollzeiten, as the adapter reads.
WITH months AS (
    SELECT CAST('20260101' AS date) AS m UNION ALL SELECT DATEADD(month, 1, m) FROM months WHERE m < '20260601'),
mapped(code, lvl) AS (SELECT code, lvl FROM #profession_level),
paid AS (
    SELECT sz.RefDienste AS shift_id, SUM(ISNULL(sz.Minuten, DATEDIFF(minute, sz.Kommt, sz.Geht))) / 60.0 AS hours
    FROM TDiensteSollzeiten sz WHERE sz.RefDienste IN (1113, 1453, 1605, 1690) GROUP BY sz.RefDienste),
need AS (
    SELECT d.planning_unit_id AS unit, DATEFROMPARTS(YEAR(d.demand_date), MONTH(d.demand_date), 1) AS m, d.staff_level AS lvl,
        SUM(d.required_count) AS slots, SUM(d.required_count * pd.hours) AS hours
    FROM dbo.StaffSchedulingDemand d JOIN paid pd ON pd.shift_id = d.shift_id
    WHERE d.planning_unit_id IN (77, 79) AND d.demand_date BETWEEN '20260101' AND '20260630'
    GROUP BY d.planning_unit_id, DATEFROMPARTS(YEAR(d.demand_date), MONTH(d.demand_date), 1), d.staff_level),
credit AS (
    SELECT t.RefPersonal, DATEFROMPARTS(YEAR(t.Datum), MONTH(t.Datum), 1) AS m, SUM(t.Wert) AS h FROM TPersonalKontenJeTag t
    WHERE t.RefKonten IN (85, 93, 95, 97) AND t.Datum BETWEEN '20260101' AND '20260630'
    GROUP BY t.RefPersonal, DATEFROMPARTS(YEAR(t.Datum), MONTH(t.Datum), 1)),
have AS (
    SELECT pep.RefPlanungseinheiten AS unit, mo.m, mm.lvl, COUNT(*) AS staff, SUM(a.Wert2 - ISNULL(c.h, 0)) AS hours
    FROM months mo JOIN TPlanungseinheitenPersonal pep ON pep.RefPlanungseinheiten IN (77, 79, 408) AND pep.IstHeimat = 1
        AND ISNULL(pep.KeinEPlan, 0) = 0 AND CONVERT(date, pep.VonDat) <= mo.m
        AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= EOMONTH(mo.m))
    JOIN TBerufe b ON b.Prim = pep.RefBerufe JOIN mapped mm ON mm.code = LTRIM(RTRIM(b.KurzBez))
    JOIN TPersonalKontenJeMonat a ON a.RefPersonal = pep.RefPersonal AND a.RefKonten = 1 AND a.Monat = YEAR(mo.m) * 100 + MONTH(mo.m)
    LEFT JOIN credit c ON c.RefPersonal = pep.RefPersonal AND c.m = mo.m
    GROUP BY pep.RefPlanungseinheiten, mo.m, mm.lvl)
SELECT COALESCE(n.unit, h.unit) AS unit, COALESCE(n.m, h.m) AS month, COALESCE(n.lvl, h.lvl) AS level, ISNULL(n.slots, 0) AS demand_slots,
    ROUND(ISNULL(n.hours, 0), 1) AS demand_h, ISNULL(h.staff, 0) AS home_staff, ROUND(ISNULL(h.hours, 0), 1) AS available_h,
    CASE WHEN ISNULL(n.hours, 0) = 0 THEN NULL ELSE ROUND(ISNULL(h.hours, 0) / n.hours, 2) END AS ratio
FROM need n FULL JOIN have h ON h.unit = n.unit AND h.m = n.m AND h.lvl = n.lvl
ORDER BY month, unit, level
