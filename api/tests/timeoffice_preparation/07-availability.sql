-- Project availability of the 96 employees of the planned units, and no wishes: the example schedules are
-- generated without wishes.
-- Writes: 7 StaffSchedulingAvailability rows (791 unavailable on his native duty dates 2026-06-08 to 12; two
-- available_only days) and deletes every StaffSchedulingWish row of these employees. Inserts, updates and deletes inside
-- 2026-01-01 to 2026-06-30 for these employees only.
-- Converges: rerunning leaves exactly these inputs and changes no row; run by tests/test_timeoffice_preparation.py,
-- which applies each file in one transaction and refuses it unless every read-back `ok` is 1.

SELECT v.emp, v.day, v.kind, v.shift_ids, v.reason INTO #availability FROM (VALUES
    (791, '20260608', N'unavailable', NULL, N'TimeOffice-Dienst T28/T33 im Zielplan'),
    (791, '20260609', N'unavailable', NULL, N'TimeOffice-Dienst T28/T33 im Zielplan'),
    (791, '20260610', N'unavailable', NULL, N'TimeOffice-Dienst T28/T33 im Zielplan'),
    (791, '20260611', N'unavailable', NULL, N'TimeOffice-Dienst T28/T33 im Zielplan'),
    (791, '20260612', N'unavailable', NULL, N'TimeOffice-Dienst T28/T33 im Zielplan'),
    (917, '20260310', N'available_only', N'[1113]', N'Nur Frühdienst (Beispiel)'),
    (1143, '20260414', N'available_only', N'[1113, 1453]', N'Nur Früh- oder Zwischendienst (Beispiel)')
) v(emp, day, kind, shift_ids, reason)
GO
DELETE a FROM dbo.StaffSchedulingAvailability a
WHERE a.employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND a.availability_date BETWEEN '20260101' AND '20260630'
    AND NOT EXISTS (SELECT 1 FROM #availability v WHERE v.emp = a.employee_id AND v.day = a.availability_date)
GO
UPDATE a SET availability_type = v.kind, shift_ids = v.shift_ids, reason = v.reason
FROM dbo.StaffSchedulingAvailability a JOIN #availability v ON a.employee_id = v.emp AND a.availability_date = v.day
WHERE a.availability_type <> v.kind OR ISNULL(a.shift_ids, N'') <> ISNULL(v.shift_ids, N'') OR ISNULL(a.reason, N'') <> ISNULL(v.reason, N'')
GO
INSERT INTO dbo.StaffSchedulingAvailability (employee_id, availability_date, availability_type, shift_ids, reason)
SELECT v.emp, v.day, v.kind, v.shift_ids, v.reason FROM #availability v
WHERE NOT EXISTS (SELECT 1 FROM dbo.StaffSchedulingAvailability a WHERE a.employee_id = v.emp AND a.availability_date = v.day)
GO
DELETE w FROM dbo.StaffSchedulingWish w
WHERE w.employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND w.wish_date BETWEEN '20260101' AND '20260630'
GO
SELECT (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability a JOIN #availability v ON a.employee_id = v.emp
        AND a.availability_date = v.day AND a.availability_type = v.kind AND ISNULL(a.shift_ids, N'') = ISNULL(v.shift_ids, N'')) AS availability,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability WHERE employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND availability_date BETWEEN '20260101' AND '20260630') AS availability_in_scope,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingWish WHERE employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND wish_date BETWEEN '20260101' AND '20260630') AS wishes,
    CASE WHEN (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability a JOIN #availability v ON a.employee_id = v.emp
        AND a.availability_date = v.day AND a.availability_type = v.kind AND ISNULL(a.shift_ids, N'') = ISNULL(v.shift_ids, N'')) = 7
        AND (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability WHERE employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND availability_date BETWEEN '20260101' AND '20260630') = 7
        AND (SELECT COUNT(*) FROM dbo.StaffSchedulingWish WHERE employee_id IN (459, 790, 791, 803, 818, 835, 839, 843, 844, 914, 917, 918, 921, 924, 925, 927, 928, 941, 946, 1138, 1143, 1144, 1147, 1150, 1161, 1167, 1175, 1184, 1191, 1199, 1200, 1203, 1209, 1218, 1224, 1226, 1229, 1230, 1231, 1238, 1474, 2932, 2939, 2946, 2963, 3463, 3566, 3642, 3868, 4064, 4073, 4081, 4082, 4083, 4100, 4101, 4158, 5002, 5318, 5367, 5844, 5866, 5920, 6259, 6266, 6318, 6330, 6724, 6727, 6773, 6836, 6928, 6977, 6995, 7006, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7490, 7496, 7603, 7606, 7660, 7741, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND wish_date BETWEEN '20260101' AND '20260630') = 0
        THEN 1 ELSE 0 END AS ok
GO
DROP TABLE #availability
