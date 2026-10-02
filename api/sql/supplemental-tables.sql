-- Project tables next to the TimeOffice schema. An authorized preparer runs this
-- file once against the prepared test database; the API never creates tables.
-- It is for a database without these tables; see the TimeOffice adapter docs for
-- migrating an evidence table from the earlier script with a constraints column.
-- The runtime login needs SELECT on all five tables and INSERT/DELETE on the
-- availability, wish and both demand tables.

-- An evidence row declares an employee's complete verified monthly credits.
-- An empty JSON array is explicit verified absence of credits, never a default.
CREATE TABLE dbo.StaffSchedulingEmployeeMonthEvidence (
    employee_id int NOT NULL CHECK (employee_id > 0),
    planning_month date NOT NULL,
    credit_details nvarchar(max) NOT NULL CHECK (ISJSON(credit_details) = 1),
    source nvarchar(500) NOT NULL CHECK (LEN(source) > 0),
    PRIMARY KEY (employee_id, planning_month),
    CHECK (DAY(planning_month) = 1)
);

-- Project availability, edited in the webapp. Native TimeOffice absences stay
-- in the roster tables and are read separately.
CREATE TABLE dbo.StaffSchedulingAvailability (
    employee_id int NOT NULL CHECK (employee_id > 0),
    availability_date date NOT NULL,
    availability_type nvarchar(32) NOT NULL
        CHECK (availability_type IN (N'unavailable', N'vacation', N'training', N'free_day', N'available_only')),
    -- JSON array of canonical shift IDs; only for available_only.
    shift_ids nvarchar(200) NULL CHECK (shift_ids IS NULL OR ISJSON(shift_ids) = 1),
    reason nvarchar(500) NULL,
    PRIMARY KEY (employee_id, availability_date),
    CHECK ((availability_type = N'available_only' AND shift_ids IS NOT NULL)
        OR (availability_type <> N'available_only' AND shift_ids IS NULL))
);

-- Soft wishes. They are stored and shown but do not influence generation.
CREATE TABLE dbo.StaffSchedulingWish (
    employee_id int NOT NULL CHECK (employee_id > 0),
    wish_date date NOT NULL,
    wish_type nvarchar(32) NOT NULL
        CHECK (wish_type IN (N'free_day', N'free_shift', N'preferred_day', N'preferred_shift')),
    shift_id int NULL CHECK (shift_id > 0),
    PRIMARY KEY (employee_id, wish_date)
);

-- Dated minimum staffing. A month row declares that the station's demand for
-- that month is saved; within it, a missing requirement row means nobody.
CREATE TABLE dbo.StaffSchedulingDemandMonth (
    planning_unit_id int NOT NULL CHECK (planning_unit_id > 0),
    planning_month date NOT NULL CHECK (DAY(planning_month) = 1),
    PRIMARY KEY (planning_unit_id, planning_month)
);

CREATE TABLE dbo.StaffSchedulingDemand (
    planning_unit_id int NOT NULL,
    demand_date date NOT NULL,
    shift_id int NOT NULL CHECK (shift_id > 0),
    staff_level nvarchar(32) NOT NULL CHECK (staff_level IN (N'professional', N'assistant', N'trainee', N'mfa')),
    required_count int NOT NULL CHECK (required_count > 0),
    PRIMARY KEY (planning_unit_id, demand_date, shift_id, staff_level)
);
