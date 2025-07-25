--8<--
user-view/list-of-conditions.md:minimize-hidden-employees
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/minimize_hidden_employees.py"

    possible_hidden_employee_variables.append(possible_hidden_employee_variable)

return sum(possible_hidden_employee_variables) * self._weight
```

We minimize the total number of assigned shifts of all hidden employees.
