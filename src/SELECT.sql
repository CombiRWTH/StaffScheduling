SELECT
    pep.RefPlanungseinheiten AS planning_unit_id,
    b.KurzBez AS profession_code,
    b.Bezeichnung AS profession_name,
    COUNT(DISTINCT pep.RefPersonal) AS employee_count,
    STRING_AGG(CONVERT(varchar(20), pep.RefPersonal), ', ') AS employee_ids
FROM TPlanungseinheitenPersonal pep
JOIN TBerufe b
    ON b.Prim = pep.RefBerufe
WHERE pep.RefPlanungseinheiten IN (77, 78)
    AND CONVERT(date, pep.VonDat) <= '2024-11-30'
    AND (
        pep.BisDat IS NULL
        OR CONVERT(date, pep.BisDat) >= '2024-11-01'
    )
    AND ISNULL(pep.KeinEPlan, 0) = 0
GROUP BY
    pep.RefPlanungseinheiten,
    b.KurzBez,
    b.Bezeichnung
ORDER BY
    pep.RefPlanungseinheiten,
    b.KurzBez;
