-- Project availability and a small demonstration wish set for the 53 employees of 77, 79 and 408.
-- Writes: 7 StaffSchedulingAvailability rows (791 unavailable on his native duty dates 2026-06-08 to 12; two
-- available_only days) and 32 StaffSchedulingWish rows (two per station and month, one jumper pool wish per
-- month, two that conflict with availability). Inserts, updates and deletes inside 2026-01-01 to 2026-06-30
-- for these employees only.
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
SELECT v.emp, v.day, v.kind, v.shift INTO #wish FROM (VALUES
    (921, '20260110', N'free_day', NULL),
    (924, '20260121', N'preferred_shift', 1113),
    (844, '20260102', N'free_shift', 1690),
    (4064, '20260119', N'preferred_day', NULL),
    (8046, '20260125', N'free_day', NULL),
    (925, '20260214', N'free_day', NULL),
    (928, '20260218', N'preferred_shift', 1113),
    (1138, '20260206', N'free_shift', 1690),
    (4158, '20260216', N'preferred_day', NULL),
    (8047, '20260222', N'free_day', NULL),
    (1229, '20260314', N'free_day', NULL),
    (1230, '20260318', N'preferred_shift', 1113),
    (1143, '20260306', N'free_shift', 1690),
    (5002, '20260316', N'preferred_day', NULL),
    (8048, '20260322', N'free_day', NULL),
    (2932, '20260411', N'free_day', NULL),
    (2963, '20260415', N'preferred_shift', 1113),
    (1150, '20260403', N'free_shift', 1690),
    (6330, '20260420', N'preferred_day', NULL),
    (8049, '20260426', N'free_day', NULL),
    (3566, '20260509', N'free_day', NULL),
    (3868, '20260520', N'preferred_shift', 1113),
    (1161, '20260501', N'free_shift', 1690),
    (7131, '20260518', N'preferred_day', NULL),
    (8050, '20260524', N'free_day', NULL),
    (6266, '20260613', N'free_day', NULL),
    (6727, '20260617', N'preferred_shift', 1113),
    (1226, '20260605', N'free_shift', 1690),
    (7132, '20260615', N'preferred_day', NULL),
    (8051, '20260628', N'free_day', NULL),
    (917, '20260310', N'preferred_shift', 1605),
    (818, '20260325', N'preferred_day', NULL)
) v(emp, day, kind, shift)
GO
DELETE a FROM dbo.StaffSchedulingAvailability a
WHERE a.employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND a.availability_date BETWEEN '20260101' AND '20260630'
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
WHERE w.employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND w.wish_date BETWEEN '20260101' AND '20260630'
    AND NOT EXISTS (SELECT 1 FROM #wish v WHERE v.emp = w.employee_id AND v.day = w.wish_date)
GO
UPDATE w SET wish_type = v.kind, shift_id = v.shift
FROM dbo.StaffSchedulingWish w JOIN #wish v ON w.employee_id = v.emp AND w.wish_date = v.day
WHERE w.wish_type <> v.kind OR ISNULL(w.shift_id, 0) <> ISNULL(v.shift, 0)
GO
INSERT INTO dbo.StaffSchedulingWish (employee_id, wish_date, wish_type, shift_id)
SELECT v.emp, v.day, v.kind, v.shift FROM #wish v
WHERE NOT EXISTS (SELECT 1 FROM dbo.StaffSchedulingWish w WHERE w.employee_id = v.emp AND w.wish_date = v.day)
GO
SELECT (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability a JOIN #availability v ON a.employee_id = v.emp
        AND a.availability_date = v.day AND a.availability_type = v.kind AND ISNULL(a.shift_ids, N'') = ISNULL(v.shift_ids, N'')) AS availability,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingWish w JOIN #wish v ON w.employee_id = v.emp AND w.wish_date = v.day
        AND w.wish_type = v.kind AND ISNULL(w.shift_id, 0) = ISNULL(v.shift, 0)) AS wishes,
    (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability WHERE employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND availability_date BETWEEN '20260101' AND '20260630')
        + (SELECT COUNT(*) FROM dbo.StaffSchedulingWish WHERE employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND wish_date BETWEEN '20260101' AND '20260630') AS scope_total,
    CASE WHEN (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability a JOIN #availability v ON a.employee_id = v.emp
        AND a.availability_date = v.day AND a.availability_type = v.kind AND ISNULL(a.shift_ids, N'') = ISNULL(v.shift_ids, N'')) = 7
        AND (SELECT COUNT(*) FROM dbo.StaffSchedulingWish w JOIN #wish v ON w.employee_id = v.emp AND w.wish_date = v.day
        AND w.wish_type = v.kind AND ISNULL(w.shift_id, 0) = ISNULL(v.shift, 0)) = 32
        AND (SELECT COUNT(*) FROM dbo.StaffSchedulingAvailability WHERE employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND availability_date BETWEEN '20260101' AND '20260630')
        + (SELECT COUNT(*) FROM dbo.StaffSchedulingWish WHERE employee_id IN (790, 791, 818, 844, 914, 917, 921, 924, 925, 927, 928, 1138, 1143, 1150, 1161, 1226, 1229, 1230, 2932, 2963, 3463, 3566, 3868, 4064, 4158, 5002, 5318, 5367, 6266, 6330, 6727, 6836, 6928, 6995, 7028, 7124, 7131, 7132, 7207, 7375, 7378, 7496, 7603, 7606, 7660, 7919, 8046, 8047, 8048, 8049, 8050, 8051, 8052) AND wish_date BETWEEN '20260101' AND '20260630')
        = 39 THEN 1 ELSE 0 END AS ok
GO
DROP TABLE #availability
GO
DROP TABLE #wish
