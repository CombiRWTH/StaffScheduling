--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Weights Configuration

Weights control the relative importance of soft optimization objectives. Since real-world hospital goals often compete with one another (for example, granting every employee wish versus keeping overtime strictly minimal), the solver uses these weights to prioritize trade-offs.

#### Available Objective Weights

| Key | Default Weight | Clinical Purpose |
|---|:---:|---|
| `wishes` | `3` | Fulfill employee shift wishes and preferred days off. |
| `overtime` | `4` | Minimize deviations from monthly contracted working hours. |
| `fairness` | `3` | Equitably distribute wishes and night shifts among all eligible nurses. |
| `free_weekend` | `3` | Maximize complete free weekends (both Saturday and Sunday off). |
| `second_weekend` | `1` | Enforce alternating weekends off (working at most every second weekend). |
| `consecutive_nights` | `2` | Penalize prolonged streaks of consecutive night shifts. |
| `after_night` | `3` | Ensure adequate recovery days following a night shift phase. |
| `consecutive_days` | `1` | Avoid excessive consecutive working days without a rest day. |
| `rotate` | `1` | Encourage forward, clockwise shift progression (Early $\rightarrow$ Late $\rightarrow$ Night). |

#### Configuration in Practice

* **Web Interface (StaffSchedulingWeb):** The preferred method is to adjust the weight sliders in the **Weights** section of the web interface. Changes are saved directly to the database via `PUT /weights`.
* **Offline / Light Mode:** Weights are loaded from `cases/{case_id}/{MM_YYYY}/weights.json`. If this file is omitted, the built-in defaults shown above are used automatically.

Example `weights.json`:

```json
{
    "wishes": 3,
    "overtime": 4,
    "fairness": 3,
    "free_weekend": 3,
    "second_weekend": 1,
    "consecutive_nights": 2,
    "after_night": 3,
    "consecutive_days": 1,
    "rotate": 1
}
```

Higher weight values prioritize an objective more aggressively during the CP-SAT optimization process. A weight of `0` effectively turns off penalties for that objective.
