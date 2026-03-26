--8<--
user-view/list-of-conditions.md:every-second-weekend-free
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/every_second_weekend_free.py"

# Weekend is free only if both Saturday AND Sunday are free
model.add(w1_sat_var + w1_sun_var == 0).only_enforce_if(w1_free)
model.add(w1_sat_var + w1_sun_var >= 1).only_enforce_if(w1_free.Not())

model.add(w2_sat_var + w2_sun_var == 0).only_enforce_if(w2_free)
model.add(w2_sat_var + w2_sun_var >= 1).only_enforce_if(w2_free.Not())
same_status_penalty = model.new_bool_var(f"same_status_penalty_e:{employee.get_key()}_i:{i}")

# Penalty = 1 if (w1_free AND w2_free) OR (NOT w1_free AND NOT w2_free)
model.add(same_status_penalty == 1).only_enforce_if([w1_free, w2_free])
model.add(same_status_penalty == 1).only_enforce_if([w1_free.Not(), w2_free.Not()])

penalties.append(same_status_penalty)
```

The code above is executed for each employee for each weekend.
