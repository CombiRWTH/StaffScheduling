WITH selected_employees AS (
    SELECT DISTINCT pp.RefPersonal AS employee_id
    FROM TPlanPersonal pp
    WHERE pp.RefPlan IN (17916, 17045)
)
SELECT
    se.employee_id,
    COUNT(DISTINCT CAST(pkt.Datum AS date)) AS worked_sundays
FROM selected_employees se
LEFT JOIN TPersonalKontenJeTag pkt
    ON pkt.RefPersonal = se.employee_id
   AND pkt.RefKonten = 40
   AND pkt.Datum BETWEEN CONVERT(date, '2023-11-30', 23)
                     AND CONVERT(date, '2024-11-30', 23)
   AND DATEDIFF(day, CONVERT(date, '1900-01-07', 23), CAST(pkt.Datum AS date)) % 7 = 0
   AND ISNULL(pkt.Wert, 0) > 0
GROUP BY se.employee_id
ORDER BY worked_sundays DESC, se.employee_id;
