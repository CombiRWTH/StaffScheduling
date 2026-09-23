--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Weights Configuration

Weights control the relative importance of soft optimization objectives. Since real-world hospital goals often compete with one another (for example, granting every employee wish versus keeping overtime strictly minimal), the solver uses these weights to prioritize trade-offs.

#### Available Objective Weights

| Frontend / API Key | Domain Field Name | Default Weight | Clinical Purpose |
|---|---|:---:|---|
| `wishes` | `employee_wish` | `3` | Fulfill employee shift wishes and preferred days off. |
| `overtime` | `overtime_penalty` | `4` | Minimize deviations from monthly contracted working hours. |
| `fairness` | `fairness` | `3` | Equitably distribute wishes and night shifts among all eligible nurses. |
| `free_weekend` | `free_weekend` | `3` | Maximize complete free weekends (both Saturday and Sunday off). |
| `second_weekend` | `second_weekend_penalty` | `1` | Enforce alternating weekends off (working at most every second weekend). |
| `consecutive_nights` | `consecutive_night_shifts` | `2` | Penalize prolonged streaks of consecutive night shifts. |
| `after_night` | `recovery_after_night_shift` | `3` | Ensure adequate recovery days following a night shift phase. |
| `consecutive_days` | `consecutive_working_days` | `1` | Avoid excessive consecutive working days without a rest day. |
| `rotate` | `shift_rotation` | `1` | Encourage forward, clockwise shift progression (Early $\rightarrow$ Late $\rightarrow$ Night). |
| `hidden` | `hidden_employee` | `100` | Balance generated shifts fairly across eligible staff rather than concentrating load on few employees. |

#### Configuration in Practice

* **Web Interface (StaffSchedulingWeb):** The preferred method is to adjust the weight sliders in the **Weights** section of the web interface. Changes are sent via `PUT /weights` using the frontend keys above.
* **REST API:** Direct API calls use the frontend key format in the request body (e.g. `{"data": {"wishes": 3, "overtime": 4, ...}}`).
* **Offline / Light Mode:** Case files contain no weight configuration. Weights are stored per planning unit in TimeOffice; when nothing is stored, the built-in defaults shown above are used automatically.

Full example of a `PUT /weights` request body (frontend keys, wrapped in `data`):

```json
{
    "data": {
        "wishes": 3,
        "overtime": 4,
        "fairness": 3,
        "free_weekend": 3,
        "second_weekend": 1,
        "consecutive_nights": 2,
        "after_night": 3,
        "consecutive_days": 1,
        "rotate": 1,
        "hidden": 100
    }
}
```

Higher weight values prioritize an objective more aggressively during the CP-SAT optimization process. A weight of `0` effectively turns off penalties for that objective.
