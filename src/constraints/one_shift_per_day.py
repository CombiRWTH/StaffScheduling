from constraint import Constraint
from model import Model


class OneShiftPerDay(Constraint):
    def __init__(self, employees, days, shifts):
        super().__init__(employees, days, shifts)

    def add_to_model(self, model: Model):
        for employee in self.employees:
            for day in self.days:
                model.add_at_most_one(
                    model.get_variable(employee, day, shift) for shift in self.shifts
                )

    def get_key() -> str:
        return "one-shift-per-key"

    def get_name() -> str:
        return "One Shift per Day"
