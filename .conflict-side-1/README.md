# StaffScheduling 🗓️

## Documentation 📖

To explore the documentation, you can either view it online or run it locally.
- **Online Documentation 🌐**

  You can view the online documentation [here](https://combirwth.github.io/StaffScheduling/).

- **Local Documentation 📚**

  ```shell
  uv sync --extra docs
  uv run mkdocs serve
  ```
  Keep in mind to check the [pre-requisites](https://combirwth.github.io/StaffScheduling/getting-started/prerequisites) for the project before running the documentation locally.

## Usage 🚀

- **Running the Solver 🧩**

  ```shell
  uv run algorithm/solving.py
  ```


### Command-Line Arguments

This script solves a **staff scheduling** problem over a rolling planning horizon.

#### Usage

```bash
uv run algorithm/solving.py [--case_id CASE_ID] [--num_days NUM_DAYS] [--output OUTPUT ...]
```

#### Arguments

* `--case_id`, `-c`
  *(int, default: 1)*
  ID of the case folder to load scheduling data from.

* `--num_days`, `-n`
  *(int, default: 30)*
  Number of days to include in the planning horizon.

* `--output`, `-o`
  *(one or more values, default: \["json"])*
  Output formats. Supported options:

  * `json` – Save the schedule as a JSON file
  * `plot` – Show a visual plot of the schedule
  * `print` – Print the schedule to the console

#### Example

```bash
uv run algorithm/solving.py -c 1 -n 14 -o json plot
```

This will plan for 14 days using case folder 1 and produce both JSON and plot outputs.
