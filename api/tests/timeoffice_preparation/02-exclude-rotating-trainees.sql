-- Exclude rotating trainees from planning: their home is a school unit outside the planned units and they
-- are members for part of a month only.
-- Writes: KeinEPlan 1 on the 15 listed non-home TPlanungseinheitenPersonal rows; nothing else.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

UPDATE pep SET KeinEPlan = 1
FROM TPlanungseinheitenPersonal pep
JOIN (VALUES
    (77, 6538, '20260511'),
    (77, 6614, '20260219'),
    (77, 6671, '20260105'),
    (77, 6673, '20260511'),
    (77, 6713, '20260219'),
    (77, 7746, '20251211'),
    (77, 7746, '20260319'),
    (79, 3004, '20251229'),
    (79, 6616, '20260511'),
    (79, 6671, '20260511'),
    (79, 6715, '20260219'),
    (79, 7743, '20260526'),
    (79, 7770, '20260526'),
    (79, 7771, '20260119'),
    (79, 7789, '20260526')
) v(unit, emp, von) ON pep.RefPlanungseinheiten = v.unit AND pep.RefPersonal = v.emp AND pep.VonDat = v.von
WHERE ISNULL(pep.KeinEPlan, 0) <> 1 AND ISNULL(pep.IstHeimat, 0) = 0
GO
SELECT COUNT(*) AS excluded, CASE WHEN COUNT(*) = 15 THEN 1 ELSE 0 END AS ok
FROM TPlanungseinheitenPersonal pep
JOIN (VALUES
    (77, 6538, '20260511'),
    (77, 6614, '20260219'),
    (77, 6671, '20260105'),
    (77, 6673, '20260511'),
    (77, 6713, '20260219'),
    (77, 7746, '20251211'),
    (77, 7746, '20260319'),
    (79, 3004, '20251229'),
    (79, 6616, '20260511'),
    (79, 6671, '20260511'),
    (79, 6715, '20260219'),
    (79, 7743, '20260526'),
    (79, 7770, '20260526'),
    (79, 7771, '20260119'),
    (79, 7789, '20260526')
) v(unit, emp, von) ON pep.RefPlanungseinheiten = v.unit AND pep.RefPersonal = v.emp AND pep.VonDat = v.von
WHERE pep.KeinEPlan = 1
