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

# --8<-- [start:Solving]
### 1. Solving

After installing dependencies, you can start solving staff scheduling problems by running
```bash
uv run staff-scheduling solve 3
```
The three corresponds to the `case_id` meaning in the folder `cases/3`. If you want to create your own case
simply copy the folder 3 and rename it to another integer. Then you can change the number of employees etc., see [configuration](/StaffScheduling/user-view/configuration/).

The algorithm needs 5 minutes to find a solution.
# --8<-- [end:Solving]

# --8<-- [start:Viewing]
### 2. Viewing
After the algorithm found a solution you can view it by running
```bash
uv run staff-scheduling plot 3
```
If you have created your own case, you need to change the integer `3` to your new case.
You can then view the solution by opening the link you see in the terminal, probably [http://127.0.0.1:5020](http://127.0.0.1:5020).
# --8<-- [end:Viewing]
