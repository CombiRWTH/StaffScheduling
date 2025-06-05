from employee import Employee
from variable import Variable


class EmployeeDayShift(Variable):
    def __init__(self, employees: list[Employee]):
        self.variables = {}
        self.employees = employees

    def add_to_model(self, model):
        for employee in self.employees:
            self.variables
