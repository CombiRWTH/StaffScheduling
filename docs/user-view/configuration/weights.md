--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Weights Configuration

Weights control the relative importance of optimization objectives (for example overtime vs. wishes).

Current behavior:

- If present, weights are loaded from `cases/{case_id}/{MM_YYYY}/weights.json`.
- If that file is missing, built-in defaults are used.

Example file:

```json
{
    "free_weekend": 2,
    "consecutive_nights": 2,
    "hidden": 100,
    "hidden_count": 1000000,
    "overtime": 4,
    "consecutive_days": 1,
    "rotate": 1,
    "wishes": 3,
    "after_night": 3,
    "second_weekend": 1
}
```

Use larger values to prioritize an objective more strongly. Values can be `0` or fractional if desired.

When using StaffSchedulingWeb, the preferred way is to adjust weights in the UI.
