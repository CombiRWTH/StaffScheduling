-- Run explicitly against an authorized prepared test database before inspection.
-- An evidence row declares complete verified monthly credits and additional hard
-- restrictions. Empty JSON arrays are explicit verified absence, never defaults.
CREATE TABLE dbo.StaffSchedulingEmployeeMonthEvidence (
    employee_id int NOT NULL CHECK (employee_id > 0),
    planning_month date NOT NULL,
    credit_details nvarchar(max) NOT NULL CHECK (ISJSON(credit_details) = 1),
    hard_restrictions nvarchar(max) NOT NULL CHECK (ISJSON(hard_restrictions) = 1),
    source nvarchar(500) NOT NULL CHECK (LEN(source) > 0),
    PRIMARY KEY (employee_id, planning_month),
    CHECK (DAY(planning_month) = 1)
);
