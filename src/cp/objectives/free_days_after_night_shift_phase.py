import logging

class FreeDaysAfterNightShiftPhaseObjective:
    KEY = "FreeDaysAfterNightShiftPhase"

    def __init__(self, weight, employees, days, shifts):
        self.weight = weight
        self.employees = employees
        self.days = days
        self.shifts = shifts

    def score(self, solution):
        score = 0
        for employee in self.employees:
            emp_id = employee["PersNr"]
            for day in range(len(self.days) - 2):
                shift_today = solution.get((emp_id, day))
                shift_next = solution.get((emp_id, day + 1))
                shift_after = solution.get((emp_id, day + 2))

                if shift_today == "N":
                    if shift_next is None and shift_after is None:
                        logging.debug(f"Employee {emp_id} has 48h rest after day {day}")
                        score += 1

        logging.info(f"[FreeDaysAfterNightShiftPhaseObjective] Raw score: {score}, weighted: {self.weight * score}")
        return self.weight * score
