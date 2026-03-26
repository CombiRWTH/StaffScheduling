--8<--
user-view/list-of-conditions.md:maximize-wishes
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/maximize_wishes.py"
for ...
    for ...
        penalties.append(penalty)

return cast(LinearExpr, sum(penalties)) * self.weight
```

For each employee we penalize all wished shifts or days that are not granted.
