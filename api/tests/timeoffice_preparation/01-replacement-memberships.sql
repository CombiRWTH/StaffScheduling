-- Replacement memberships of the jumper pool staff at the stations they serve: 408 at all seven stations, 68 at
-- 78, 83, 85, 88 and 337.
-- Writes: 109 TPlanungseinheitenPersonal rows (2025-12-01 to 2026-07-31), IstVonErsatz 1, with the profession of
-- each employee's home membership at their jumper pool covering that period. Inserts missing rows only.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

SELECT v.emp, v.unit, v.pool INTO #replacement FROM (VALUES
    (8046, 77, 408),
    (8046, 79, 408),
    (8047, 77, 408),
    (8047, 79, 408),
    (8048, 77, 408),
    (8048, 79, 408),
    (8049, 77, 408),
    (8049, 79, 408),
    (8050, 77, 408),
    (8050, 79, 408),
    (8051, 77, 408),
    (8051, 79, 408),
    (8052, 77, 408),
    (8052, 79, 408),
    (835, 78, 68),
    (835, 83, 68),
    (835, 85, 68),
    (835, 88, 68),
    (835, 337, 68),
    (839, 78, 68),
    (839, 83, 68),
    (839, 85, 68),
    (839, 88, 68),
    (839, 337, 68),
    (843, 78, 68),
    (843, 83, 68),
    (843, 85, 68),
    (843, 88, 68),
    (843, 337, 68),
    (918, 78, 68),
    (918, 83, 68),
    (918, 85, 68),
    (918, 88, 68),
    (918, 337, 68),
    (1218, 78, 68),
    (1218, 83, 68),
    (1218, 85, 68),
    (1218, 88, 68),
    (1218, 337, 68),
    (5844, 78, 68),
    (5844, 83, 68),
    (5844, 85, 68),
    (5844, 88, 68),
    (5844, 337, 68),
    (6259, 78, 68),
    (6259, 83, 68),
    (6259, 85, 68),
    (6259, 88, 68),
    (6259, 337, 68),
    (6318, 78, 68),
    (6318, 83, 68),
    (6318, 85, 68),
    (6318, 88, 68),
    (6318, 337, 68),
    (6724, 78, 68),
    (6724, 83, 68),
    (6724, 85, 68),
    (6724, 88, 68),
    (6724, 337, 68),
    (7006, 78, 68),
    (7006, 83, 68),
    (7006, 85, 68),
    (7006, 88, 68),
    (7006, 337, 68),
    (7490, 78, 68),
    (7490, 83, 68),
    (7490, 85, 68),
    (7490, 88, 68),
    (7490, 337, 68),
    (7741, 78, 68),
    (7741, 83, 68),
    (7741, 85, 68),
    (7741, 88, 68),
    (7741, 337, 68),
    (8046, 78, 408),
    (8046, 83, 408),
    (8046, 85, 408),
    (8046, 88, 408),
    (8046, 337, 408),
    (8047, 78, 408),
    (8047, 83, 408),
    (8047, 85, 408),
    (8047, 88, 408),
    (8047, 337, 408),
    (8048, 78, 408),
    (8048, 83, 408),
    (8048, 85, 408),
    (8048, 88, 408),
    (8048, 337, 408),
    (8049, 78, 408),
    (8049, 83, 408),
    (8049, 85, 408),
    (8049, 88, 408),
    (8049, 337, 408),
    (8050, 78, 408),
    (8050, 83, 408),
    (8050, 85, 408),
    (8050, 88, 408),
    (8050, 337, 408),
    (8051, 78, 408),
    (8051, 83, 408),
    (8051, 85, 408),
    (8051, 88, 408),
    (8051, 337, 408),
    (8052, 78, 408),
    (8052, 83, 408),
    (8052, 85, 408),
    (8052, 88, 408),
    (8052, 337, 408)
) v(emp, unit, pool)
GO
INSERT INTO TPlanungseinheitenPersonal (RefPersonal, RefPlanungseinheiten, RefBerufe, VonDat, BisDat, IstVonErsatz,
    PersonalSort, IstAusVorplanung, KeinJahresplan, IstHeimat, ImportLoeschSchutzJN, KeinEPlan)
SELECT v.emp, v.unit, h.RefBerufe, '20251201', '20260731', 1, v.emp, 0, 0, 0, 0, 0
FROM #replacement v
JOIN TPlanungseinheitenPersonal h ON h.RefPersonal = v.emp AND h.RefPlanungseinheiten = v.pool AND h.IstHeimat = 1
    AND h.VonDat <= '20251201' AND h.BisDat >= '20260731'
WHERE NOT EXISTS (SELECT 1 FROM TPlanungseinheitenPersonal x
    WHERE x.RefPersonal = v.emp AND x.RefPlanungseinheiten = v.unit AND x.VonDat = '20251201')
GO
SELECT COUNT(*) AS present, CASE WHEN COUNT(*) = 109 THEN 1 ELSE 0 END AS ok
FROM #replacement v
JOIN TPlanungseinheitenPersonal x ON x.RefPersonal = v.emp AND x.RefPlanungseinheiten = v.unit
JOIN TPlanungseinheitenPersonal h ON h.RefPersonal = v.emp AND h.RefPlanungseinheiten = v.pool AND h.IstHeimat = 1
    AND h.VonDat <= '20251201' AND h.BisDat >= '20260731'
WHERE x.VonDat = '20251201' AND x.BisDat = '20260731' AND x.IstVonErsatz = 1 AND ISNULL(x.IstHeimat, 0) = 0
    AND ISNULL(x.KeinEPlan, 0) = 0 AND x.RefBerufe = h.RefBerufe
GO
DROP TABLE #replacement
