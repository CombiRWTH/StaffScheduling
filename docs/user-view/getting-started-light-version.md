# --8<-- [start:Prerequisites]
## Prerequisites

Before setting up the project, make sure the following tools are installed on your system:

### 1. Install [Python 3.10+](https://www.python.org/downloads/)

This project requires **Python 3.10 or higher**.

Open your terminal (Mac) or Command Prompt (Windows). Check whether and which version of python you have installed by running:

```bash
python3 --version
```

If not installed, download it from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/) and install it.

### 2. Install `uv`

uv is a fast Python package manager used to create and manage isolated environments. You can install it following the instructions in the official documentation:

[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
# --8<-- [end:Prerequisites]

---
# --8<-- [start:Installation]
## Installation

Follow these steps to set up the development environment.

### 1. Download our Project

In order to use our application you need to download the code from [Github](https://github.com/CombiRWTH/StaffScheduling). If you are familiar with Github, you can simply clone the project, if not, you can click on the green "Code" button and choose to download as zip file, which you need to unpack. Then open a command line tool (terminal or command prompt) to navigate to the project folder.

### 2. Install dependencies

Make sure [`uv`](https://github.com/astral-sh/uv) is installed.

```bash
uv sync
```

This will install all required dependencies.
# --8<-- [end:Installation]

---

## Usage

### Solve in the Web Interface

Use **StaffSchedulingWeb** to configure, start, and inspect solves in a browser:

- Open the StaffSchedulingWeb documentation: [https://julian466.github.io/StaffSchedulingWeb/](https://julian466.github.io/StaffSchedulingWeb/)
- Follow the setup and run steps there.
- Use the UI to select your case and planning period, start the solver, and inspect results.
