-- Exclude rotating trainees from planning: their home is a school unit outside the planned units and they
-- are members for part of a month only.
-- Writes: KeinEPlan 1 on the 60 listed non-home TPlanungseinheitenPersonal rows; nothing else.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

SELECT v.unit, v.emp, v.von INTO #rotating FROM (VALUES
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
    (79, 7789, '20260526'),
    (78, 6537, '20260511'),
    (78, 6672, '20260219'),
    (78, 6714, '20251201'),
    (78, 6714, '20260219'),
    (78, 7770, '20251211'),
    (78, 7770, '20260316'),
    (78, 7771, '20260526'),
    (78, 7773, '20260526'),
    (78, 7796, '20260526'),
    (78, 7877, '20260526'),
    (83, 6529, '20260511'),
    (83, 6530, '20260219'),
    (83, 6535, '20251201'),
    (83, 6604, '20251201'),
    (83, 6606, '20260511'),
    (83, 6607, '20260219'),
    (83, 6607, '20260511'),
    (83, 6675, '20260112'),
    (83, 6763, '20260219'),
    (83, 7067, '20260202'),
    (83, 7068, '20260202'),
    (83, 7771, '20251211'),
    (83, 7773, '20251211'),
    (83, 7785, '20260526'),
    (83, 7786, '20260526'),
    (83, 7788, '20260316'),
    (83, 7789, '20260107'),
    (83, 7793, '20260119'),
    (83, 7796, '20260316'),
    (83, 7801, '20260526'),
    (83, 7835, '20260526'),
    (85, 3004, '20260219'),
    (85, 6537, '20260219'),
    (85, 6614, '20251201'),
    (85, 6616, '20251201'),
    (85, 6672, '20260511'),
    (85, 6713, '20260601'),
    (85, 6769, '20260219'),
    (85, 7793, '20260526'),
    (85, 7800, '20260526'),
    (88, 3004, '20260511'),
    (88, 6614, '20260511'),
    (88, 6671, '20260219'),
    (88, 6673, '20260219'),
    (88, 6714, '20260511')
) v(unit, emp, von)
GO
UPDATE pep SET KeinEPlan = 1
FROM TPlanungseinheitenPersonal pep
JOIN #rotating v ON pep.RefPlanungseinheiten = v.unit AND pep.RefPersonal = v.emp AND pep.VonDat = v.von
WHERE ISNULL(pep.KeinEPlan, 0) <> 1 AND ISNULL(pep.IstHeimat, 0) = 0
GO
SELECT COUNT(*) AS excluded, CASE WHEN COUNT(*) = 60 THEN 1 ELSE 0 END AS ok
FROM TPlanungseinheitenPersonal pep
JOIN #rotating v ON pep.RefPlanungseinheiten = v.unit AND pep.RefPersonal = v.emp AND pep.VonDat = v.von
WHERE pep.KeinEPlan = 1
GO
DROP TABLE #rotating
