--8<--
user-view/list-of-conditions.md:hierarchy-of-intermediate-shifts
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/hierarchy_of_intermediate_shifts.py"
model.add(
    num_of_weekday_intermediate_shifts_variable
    >= num_of_weekend_intermediate_shifts_variable
)
model.add(
    num_of_weekday_intermediate_shifts_variable
    - num_of_weekend_intermediate_shifts_variable
    <= 1
)
```

The implementation of this constraint does only work in combination with another objective [Free Days Near Weekend](/docs/developer-view/conditions/free-days-near-weekend).
To somehow ensure the correct hierarchy of the assigning of the intermediate shifts we focus on the total number of intermediate shifts during the week is always greater by 1 than the total number of intermediate shifts on the weekend.

!!! warning

    Our implementation of this condition is not ideal.
    The first attempt to penalties intermediate shift on weekday and weekend was effective when used in isolation, but in combination with another objective [Free Days near Weekend](/docs/developer-view/conditions/free-days-near-weekend) it did not achieve the desired results. The current implementation does not directly enforce the strict hierachy that is desired.
