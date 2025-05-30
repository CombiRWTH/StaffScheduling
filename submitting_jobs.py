import itertools
import subprocess
import os
import re
import pandas as pd

# General Settings
CASE_ID = 2


# Constraint dictionary
constraints_short_to_long = {
    "B": "basic",
    "FreeS": "free_shifts",
    "Staff": "min_staff",
    "Tar": "target_working_min",
    "MinN": "min_night_seq",
    "NSAN": "no_shift_after_night",
    "FreeW": "free_near_weekend",
    "MFNW": "more_free_night_worker",
    "MaxC": "max_consecutive",
    "Rot": "rotate_forward",
}

constraints_long_to_short = {v: k for k, v in constraints_short_to_long.items()}

# Fixed constraints
fixed_constraints = {
    "basic": True,
    "free_shifts": False,
    "min_staff": False,
    "target_working_min": False,
    "min_night_seq": False,
    "no_shift_after_night": False,
    "free_near_weekend": True,
    "more_free_night_worker": True,
    "max_consecutive": False,
    "rotate_forward": False,
}

# Combinable constraints
combining = {
    "basic": False,
    "free_shifts": True,
    "min_staff": True,
    "target_working_min": True,
    "min_night_seq": False,
    "no_shift_after_night": False,
    "free_near_weekend": False,
    "more_free_night_worker": False,
    "max_consecutive": True,
    "rotate_forward": False,
}

# Markdown tracking file
TABLE_FILE = "job_table.md"

# Ensure log folder exists
os.makedirs("logs/test", exist_ok=True)


def load_existing_jobs():
    if not os.path.exists(TABLE_FILE):
        columns = [
            "Job",
            *constraints_long_to_short.keys(),
            "CaseID",
            "Solvable",
            "CondorID",
        ]
        return pd.DataFrame(columns=columns)

    with open(TABLE_FILE, "r") as f:
        lines = f.readlines()

    # Extract header and data lines, skipping first and last (markdown table formatting)
    header = [col.strip() for col in lines[0].strip().split("|")[1:-1]]
    data = [line.strip().split("|")[1:-1] for line in lines[2:-1]]
    df = pd.DataFrame(data, columns=header)
    return df


def save_jobs_table(df):
    df = df.sort_values(by="Job")
    with open(TABLE_FILE, "w") as f:
        f.write(df.to_markdown(index=False))


def get_next_job_name(existing_df, constraints):
    prefix = int(get_binary_encoding(existing_df, constraints), 2)
    matching = sum(
        existing_df["Job"].apply(lambda cell: int(cell.split(".")[0].strip()))
        == int(prefix)
    )
    return f"{prefix}.{matching + 1}"


def get_signature_from_row(row):
    return "+".join(
        sorted(
            [
                key
                for key in constraints_long_to_short
                if key in row and row[key].strip() == "X"
            ]
        )
    )


def run_job(command):
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    print(result)
    match = re.search(r"CondorID:\s*(\d+)", result.stdout + result.stderr)
    return match.group(1) if match else "UNKNOWN"


def get_binary_encoding(existing_df, constraints: dict):
    constraints_keys = sorted(list(constraints.keys()))
    binary_str = ""
    for key in constraints_keys:
        if constraints[key]:
            binary_str += "1"
        else:
            binary_str += "0"
    return binary_str


def main():
    existing_jobs = load_existing_jobs()
    combinable_keys = [k for k, v in combining.items() if v]

    all_jobs = []

    for r in range(len(combinable_keys) + 1):
        for combo in itertools.combinations(combinable_keys, r):
            constraints = fixed_constraints.copy()
            for c in combo:
                constraints[c] = True

            # Build short signature
            active_short = [
                constraints_long_to_short[k] for k, v in constraints.items() if v
            ]
            job_name = get_next_job_name(existing_jobs, constraints)

            constraints_str = " ".join(active_short)
            log_dir = "logs/automatic/"
            log_file = f"{job_name}-log.txt"
            error_file = f"{job_name}-error.txt"
            output_file = f"{job_name}-output.txt"

            cmd = (
                f"submit -m 6000 -L {log_dir} -l {log_file} -e {error_file} -o {output_file} "
                f"~/.local/bin/uv run algorithm/solving.py -s {constraints_str} -c {CASE_ID}"
            )
            print(cmd)
            condor_id = run_job(cmd)

            row = {
                "Job": job_name,
                **{
                    k: ("X" if constraints[k] else " ")
                    for k in constraints_long_to_short
                },
                "CaseID": CASE_ID,
                "CondorID": condor_id,
                "Solvable": "",
                "WallTime": "",
            }
            all_jobs.append(row)

    # Append and save
    new_df = pd.DataFrame(all_jobs)
    updated_df = pd.concat([existing_jobs, new_df], ignore_index=True)
    save_jobs_table(updated_df)


if __name__ == "__main__":
    main()
