-- Missing monthly target plans of the stations (status 20, monthly interval, exact month bounds) and empty trusted
-- context plans (status 30) around January-June: no duties, so every context date is free.
-- Writes: 36 TPlan rows: 22 target plans of stations 83, 85, 88 and 337, and 14 context plans of every
-- station for 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07 with day interval 4, which avoids the unique
-- (unit, VonDat, interval) index of the native month plans. Inserts missing plans only; native plans stay.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

SELECT v.unit, v.von, v.bis, v.status, v.interval_ INTO #plan FROM (VALUES
    (83, '20260101', '20260131', 20, 1),
    (83, '20260201', '20260228', 20, 1),
    (83, '20260301', '20260331', 20, 1),
    (83, '20260401', '20260430', 20, 1),
    (83, '20260501', '20260531', 20, 1),
    (83, '20260601', '20260630', 20, 1),
    (85, '20260101', '20260131', 20, 1),
    (85, '20260201', '20260228', 20, 1),
    (85, '20260301', '20260331', 20, 1),
    (85, '20260501', '20260531', 20, 1),
    (85, '20260601', '20260630', 20, 1),
    (88, '20260101', '20260131', 20, 1),
    (88, '20260201', '20260228', 20, 1),
    (88, '20260301', '20260331', 20, 1),
    (88, '20260401', '20260430', 20, 1),
    (88, '20260501', '20260531', 20, 1),
    (337, '20260101', '20260131', 20, 1),
    (337, '20260201', '20260228', 20, 1),
    (337, '20260301', '20260331', 20, 1),
    (337, '20260401', '20260430', 20, 1),
    (337, '20260501', '20260531', 20, 1),
    (337, '20260601', '20260630', 20, 1),
    (77, '20251218', '20251231', 30, 4),
    (77, '20260701', '20260707', 30, 4),
    (79, '20251218', '20251231', 30, 4),
    (79, '20260701', '20260707', 30, 4),
    (78, '20251218', '20251231', 30, 4),
    (78, '20260701', '20260707', 30, 4),
    (83, '20251218', '20251231', 30, 4),
    (83, '20260701', '20260707', 30, 4),
    (85, '20251218', '20251231', 30, 4),
    (85, '20260701', '20260707', 30, 4),
    (88, '20251218', '20251231', 30, 4),
    (88, '20260701', '20260707', 30, 4),
    (337, '20251218', '20251231', 30, 4),
    (337, '20260701', '20260707', 30, 4)
) v(unit, von, bis, status, interval_)
GO
INSERT INTO TPlan (RefPlanungseinheiten, RefPlanungsIntervalle, VonDat, BisDat, RefStati)
SELECT v.unit, v.interval_, v.von, v.bis, v.status FROM #plan v
WHERE NOT EXISTS (SELECT 1 FROM TPlan p
    WHERE p.RefPlanungseinheiten = v.unit AND p.VonDat = v.von AND p.RefPlanungsIntervalle = v.interval_)
GO
SELECT COUNT(DISTINCT p.Prim) AS plans, COUNT(k.RefPlan) AS context_roster_rows,
    CASE WHEN COUNT(DISTINCT p.Prim) = 36 AND COUNT(k.RefPlan) = 0 THEN 1 ELSE 0 END AS ok
FROM #plan v
JOIN TPlan p ON p.RefPlanungseinheiten = v.unit AND p.VonDat = v.von AND p.BisDat = v.bis AND p.RefStati = v.status
    AND p.RefPlanungsIntervalle = v.interval_
LEFT JOIN TPlanPersonalKommtGeht k ON k.RefPlan = p.Prim AND v.status = 30
GO
DROP TABLE #plan
