--8<--
user-view/list-of-conditions.md:free-days-near-weekend
--8<--

!!! tip
    In the final presentation of our project another implemenation of this was requested. More details can be found in this open [issue](https://github.com/CombiRWTH/StaffScheduling/issues/173).

### Implemented using Google's OR Tools

```python title="src/cp/objectives/free_days_near_weekend.py"

return sum(
    [
        sum(possible_free_first_day_variable) * -1 * self.weight,
        sum(possible_free_second_day_variables) * -1 * self.weight,
        sum(possible_free_both_days_variables) * -4 * self.weight,
    ]
)
```

The current implementation adds a reward for each free Friday, Saturday, or Sunday. Additionally, the day after one of those days gets a "reward" when it is free. When both days are free, a higher reward is given.
