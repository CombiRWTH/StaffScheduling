--8<--
user-view/list-of-conditions.md:every-second-weekend-free
--8<--

!!! tip "Feature Request"
    In the final presentation of our project another implemenation of [Free Days Near Weekend](./free-days-near-weekend.md) was requested. This is our new, complementary objective, but there is room for improvement. More details can be found in this open [issue](https://github.com/CombiRWTH/StaffScheduling/issues/173).

### Implemented using Google's OR Tools

```python title="src/cp/objectives/every_second_weekend_free.py"

# Penalty = 1 if (w1_free AND w2_free) OR (NOT w1_free AND NOT w2_free)
model.add(same_status_penalty == 1).only_enforce_if([w1_free, w2_free])
model.add(same_status_penalty == 1).only_enforce_if(
    [w1_free.Not(), w2_free.Not()]
)
model.add(same_status_penalty == 0).only_enforce_if(
    [w1_free, w2_free.Not()]
)
model.add(same_status_penalty == 0).only_enforce_if(
    [w1_free.Not(), w2_free]
)

penalties.append(same_status_penalty)
```

Our application will iterate through every pair of consective weekends. If both weekends have the same status, meaning both are free or both are assigned, it gets a penalty. That way we encourage weekends with different status, enforcing a alternating behaviour, if possible.
