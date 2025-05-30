import os
import re
import pandas as pd

TABLE_FILE = "job_table.md"
LOG_DIR = "logs/automatic"


def load_jobs_table():
    with open(TABLE_FILE, "r") as f:
        lines = f.readlines()

    header = [h.strip() for h in lines[0].strip().split("|")[1:-1]]
    data = [line.strip().split("|")[1:-1] for line in lines[2:] if line.strip()]
    df = pd.DataFrame(data, columns=header)
    return df


def save_jobs_table(df):
    df = df.sort_values(by="Job")
    with open(TABLE_FILE, "w") as f:
        f.write(df.to_markdown(index=False))


def extract_job_info(job_id):
    output_file = os.path.join(LOG_DIR, f"{job_id}-output.txt")

    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        return None  # skip empty or missing output

    with open(output_file, "r") as f:
        content = f.read()

    # Extract Wall time
    wall_time_match = re.search(r"Wall time\s*:\s*([\d.]+)s", content)
    wall_time = wall_time_match.group(1) + "s" if wall_time_match else ""

    # Extract number of solutions
    sol_match = re.search(r"Solutions found\s*:\s*(\d+)", content)
    solvable = "Yes" if sol_match and int(sol_match.group(1)) > 0 else "No"

    # Extract solution file path
    file_match = re.search(
        r"Solutions saved to (found_solutions/[\w\-_\.]+\.json)", content
    )
    solution_file = file_match.group(1) if file_match else ""

    return wall_time, solvable, solution_file


def main():
    df = load_jobs_table()

    for i, row in df.iterrows():
        job_id = row["Job"].strip()

        result = extract_job_info(job_id)
        if result:
            wall_time, solvable, solution_file = result
            df.at[i, "WallTime"] = wall_time
            df.at[i, "Solvable"] = solvable
            df.at[i, "Solution File"] = solution_file

    save_jobs_table(df)
    print("Job results updated.")


if __name__ == "__main__":
    main()
