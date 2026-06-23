SELECT
    pkg.RefPlan AS plan_id,
    p.RefPlanungseinheiten AS plan_planning_unit_id,
    pkg.RefPlanungseinheiten AS row_planning_unit_id,
    pkg.RefPersonal AS employee_id,
    pkg.Datum AS roster_date,
    pkg.RefDienste AS work_shift_id,
    d.KurzBez AS work_shift_code,
    d.Bezeichnung AS work_shift_name,
    pkg.RefgAbw AS global_absence_shift_id,
    pkg.RefDienstAbw AS absence_shift_id,
    pkg.lfdNr AS line_number
FROM TPlanPersonalKommtGeht pkg
LEFT JOIN TPlan p
    ON p.Prim = pkg.RefPlan
LEFT JOIN TDienste d
    ON d.Prim = pkg.RefDienste
WHERE pkg.RefPersonal = 803
    AND CONVERT(date, pkg.Datum) = '2024-11-04'
ORDER BY
    pkg.RefPlan,
    pkg.RefPlanungseinheiten,
    pkg.RefDienste,
    pkg.lfdNr;
