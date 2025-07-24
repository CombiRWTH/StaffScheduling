--8<--
user-view/getting-started-light-version.md:Prerequisites
--8<--

### 3. Install `unixodbc` (Mac only)

You can install it following the instructions in the official documentation:

[https://pypi.org/project/pyodbc/](https://pypi.org/project/pyodbc/)

---

--8<--
user-view/getting-started-light-version.md:Installation
--8<--

### 2. Set Up Pre-commit Hooks (Only if you want to change something)

We use a Git hook called pre-commit which automatically checks and corrects
format mistakes in our files. So you need to install Git hooks using pre-commit:

```bash
uv run pre-commit install
```

This enables automatic code checks (e.g., formatting, linting, whitespace trimming) on every commit.

### 3. Verify Setup

To manually run all pre-commit hooks across the entire project:

```bash
uv run pre-commit run --all-files
```

---

## Usage

### 0. Fetching
First you would need to fetch the data from the database.
For that you need to create a `.env` file in the root directory, use our template.
There you need to define the database credentials, which you should be told by your instructors.

Then you can use the `fetch` command.
```bash
uv run staff-scheduling fetch 77 2024-11-01 2024-11-30
```
This reads the data from the database from Planungseinheit 77 in November 2024 and creates a folder
in `cases/`.

--8<--
user-view/getting-started-light-version.md:Solving
--8<--

--8<--
user-view/getting-started-light-version.md:Viewing
--8<--
