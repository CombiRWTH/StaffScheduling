## 🚀 Installation

Follow these steps to set up the development environment.

### 1. 📦 Install dependencies

Make sure [`uv`](https://github.com/astral-sh/uv) is installed.

```bash
uv sync
```

This will install all required dependencies.

### 2. 🔧 Set Up Pre-commit Hooks

Install Git hooks using pre-commit:

```bash
uv run pre-commit install
```

This enables automatic code checks (e.g., formatting, linting, whitespace trimming) on every commit.

### 3. ✅ Verify Setup

To manually run all pre-commit hooks across the entire project:

```bash
uv run pre-commit run --all-files
```

Use this to validate that your environment is correctly configured and all files meet the code quality standards.

### 4. 🧪 Optional: Run Hooks Only on docs/
To check only the docs/ folder:

```bash
uv run pre-commit run --files $(find docs -type f)
```

Useful when working exclusively on documentation.

### 5. Next steps

   Proceed to the [first-steps](/getting-started/first-steps) section to start with your project.
