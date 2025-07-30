--8<--
user-view/list-of-conditions.md:maximize-wishes
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/maximize_wishes.py"

model.Add(penalty == 1).OnlyEnforceIf(var)
model.Add(penalty == 0).OnlyEnforceIf(var.Not())
penalties.append(penalty)
```

For each non hidden employee we penalties all wished shifts or days that are not granted. `var` in this case means that the employee has to work the wished day or wished shift.
