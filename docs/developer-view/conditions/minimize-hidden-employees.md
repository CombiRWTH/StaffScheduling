--8<--
user-view/list-of-conditions.md:minimize-hidden-employees
--8<--

For this purpose we have an objective to minimize the amout of hidden employees and another to minimize their working time.

!!! note The objective to minimize the amount of hidden employees is currently not in use by our implementation as we have a different mechanism in place for that.

### Implemented using Google's OR Tools

```python title="src/cp/objectives/minimize_hidden_employee_count.py"

    hidden_employee_work_vars.append(hidden_employee_is_used)

return cast(LinearExpr, sum(hidden_employee_work_vars)) * self._weight
```

```python title="src/cp/objectives/minimize_hidden_employees.py"

    possible_hidden_employee_variables.append(possible_hidden_employee_variable)

return sum(possible_hidden_employee_variables) * self._weight
```
