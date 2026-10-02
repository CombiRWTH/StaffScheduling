-- Replacement memberships of the jumper pool 408 staff at stations 77 and 79.
-- Writes: 14 TPlanungseinheitenPersonal rows (employees 8046-8052, 2025-12-01 to 2026-07-31), IstVonErsatz 1,
-- with the profession of each employee's home membership at 408. Inserts missing rows only.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

INSERT INTO TPlanungseinheitenPersonal (RefPersonal, RefPlanungseinheiten, RefBerufe, VonDat, BisDat, IstVonErsatz,
    PersonalSort, IstAusVorplanung, KeinJahresplan, IstHeimat, ImportLoeschSchutzJN, KeinEPlan)
SELECT v.emp, v.unit, h.RefBerufe, '20251201', '20260731', 1, v.emp, 0, 0, 0, 0, 0
FROM (VALUES
    (8046, 77),
    (8046, 79),
    (8047, 77),
    (8047, 79),
    (8048, 77),
    (8048, 79),
    (8049, 77),
    (8049, 79),
    (8050, 77),
    (8050, 79),
    (8051, 77),
    (8051, 79),
    (8052, 77),
    (8052, 79)
) v(emp, unit)
JOIN TPlanungseinheitenPersonal h ON h.RefPersonal = v.emp AND h.RefPlanungseinheiten = 408 AND h.IstHeimat = 1
WHERE NOT EXISTS (SELECT 1 FROM TPlanungseinheitenPersonal x
    WHERE x.RefPersonal = v.emp AND x.RefPlanungseinheiten = v.unit AND x.VonDat = '20251201')
GO
SELECT COUNT(*) AS present, CASE WHEN COUNT(*) = 14 THEN 1 ELSE 0 END AS ok
FROM TPlanungseinheitenPersonal x JOIN TPlanungseinheitenPersonal h
    ON h.RefPersonal = x.RefPersonal AND h.RefPlanungseinheiten = 408 AND h.IstHeimat = 1
WHERE x.RefPersonal IN (8046, 8047, 8048, 8049, 8050, 8051, 8052) AND x.RefPlanungseinheiten IN (77, 79)
    AND x.VonDat = '20251201' AND x.BisDat = '20260731' AND x.IstVonErsatz = 1 AND ISNULL(x.IstHeimat, 0) = 0
    AND ISNULL(x.KeinEPlan, 0) = 0 AND x.RefBerufe = h.RefBerufe
