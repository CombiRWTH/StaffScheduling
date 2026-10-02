-- Empty trusted context plans (status 30) around January-June for stations 77 and 79: no duties, so every
-- context date is free.
-- Writes: 4 TPlan rows with day interval 4 for 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07, which avoids the
-- unique (unit, VonDat, interval) index of the native month plans. Inserts missing plans only.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

INSERT INTO TPlan (RefPlanungseinheiten, RefPlanungsIntervalle, VonDat, BisDat, RefStati)
SELECT v.unit, 4, v.von, v.bis, 30
FROM (VALUES
    (77, '20251218', '20251231'),
    (77, '20260701', '20260707'),
    (79, '20251218', '20251231'),
    (79, '20260701', '20260707')
) v(unit, von, bis)
WHERE NOT EXISTS (SELECT 1 FROM TPlan p
    WHERE p.RefPlanungseinheiten = v.unit AND p.VonDat = v.von AND p.RefPlanungsIntervalle = 4)
GO
SELECT COUNT(*) AS plans, COUNT(k.RefPlan) AS roster_rows,
    CASE WHEN COUNT(DISTINCT p.Prim) = 4 AND COUNT(k.RefPlan) = 0 THEN 1 ELSE 0 END AS ok
FROM TPlan p
JOIN (VALUES
    (77, '20251218', '20251231'),
    (77, '20260701', '20260707'),
    (79, '20251218', '20251231'),
    (79, '20260701', '20260707')
) v(unit, von, bis) ON p.RefPlanungseinheiten = v.unit AND p.VonDat = v.von AND p.BisDat = v.bis
LEFT JOIN TPlanPersonalKommtGeht k ON k.RefPlan = p.Prim
WHERE p.RefStati = 30 AND p.RefPlanungsIntervalle = 4
