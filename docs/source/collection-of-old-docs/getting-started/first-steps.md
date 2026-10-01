## 👣 First Steps

After installing dependencies and setting up pre-commit, you can start solving staff scheduling problems using either of the following methods.

### 1. Usage

Currently, we have two ways to start our project

1. **▶️ Method 1: Direct Solver Script**

Run the solver directly via the main script:

```bash
uv run algorithm/solving.py [--case_id CASE_ID] [--month MONTH] [--year YEAR] [--output OUTPUT ...]
```

#### Arguments

- `--case_id`, `-c`
  _(int, default: 1)_
  ID of the case folder to load scheduling data from.

- `--month`, `-m`
  _(int, default: 11)_
  Month of the staff schedule plan.

- `--year`, `-y`
  _(int, default: 2025)_
  Year of the staff schedule plan.

- `--output`, `-o`
  _(one or more values, default: \["json"])_
  Output formats. Supported options:

  - `json` – Save the schedule as a JSON file
  - `plot` – Show a visual plot of the schedule
  - `print` – Print the schedule to the console

#### Example

```bash
uv run algorithm/solving.py -c 1 -m 11 -y 2025 -o json plot
```

This will plan for November in 2025 using case folder 1 and produce both JSON and plot outputs.

2. **⚙️ Method 2: Using the solve Command**
   If your project includes an entry point named solve (e.g. via pyproject.toml), you can use the following command after syncing dependencies:

```bash
uv sync
uv run solve
```

Both methods will execute the same underlying logic to solve the scheduling problem.
