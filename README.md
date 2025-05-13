# StaffScheduling 🗓️

## Installation ⚙️

Follow these steps to set up the project:

1. **Install `uv` 🚀**
Uv is used as a python package manager and project manager. You can install it following the instructions in the official documentation:

https://docs.astral.sh/uv/getting-started/installation/

2. **Install dependencies 📦**

```shell
uv sync
```

3. **Activate pre-commit 🔄**

```shell
uv run pre-commit install
```

3. **Done**

## Documentation 📖

- **Running the Documentation 📚**

```shell
uv run mkdocs serve
```

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
