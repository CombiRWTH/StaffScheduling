--8<--
user-view/list-of-conditions.md:planned-shift
--8<--

### Implemented in the Domain & Variable Generation

Pre-planned shifts are assignments that already exist in TimeOffice before optimization begins (such as special project shifts or pre-booked duties).

In the modern architecture, these assignments are ingested as domain `Assignment` objects with `source=AssignmentSource.PRE_PLANNED`:

1. **Dataset Ingestion:** Read from TimeOffice tables (`TPlan`, `TRaster`) into `ctx.dataset.assignments`.
2. **Variable Space Enforcement:** In [`src/scheduling/solver/cp_sat/variables.py`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/variables.py), slots with pre-planned shifts are locked, preventing the CP-SAT solver from assigning conflicting generated shifts to the same employee on that day.
3. **Audit Verification:** The post-solve audit confirms that all pre-planned assignments remain intact and unchanged in the final schedule.
