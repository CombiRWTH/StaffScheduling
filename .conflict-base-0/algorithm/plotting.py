import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


def plot_schedule(
    employees,
    schedule,
    dates,
    shift_symbols=None,
    job_colors=None,
    shift_colors=None,
):
    if shift_symbols is None:
        shift_symbols = {0: "F", 1: "S", 2: "N"}

    if job_colors is None:
        job_colors = {
            "Fachkraft": "#ADD8E6",
            "Hilfskraft": "#90EE90",
            "Azubi": "#FFDAB9",
        }

    if shift_colors is None:
        shift_colors = {
            0: "#FFCCCC",  # Morning shift (F)
            1: "#CCCCFF",  # Evening shift (S)
            2: "#CCFFCC",  # Night shift (N)
        }

    employeenames = [employee["name"] for employee in employees]
    employeejobs = [employee["type"] for employee in employees]

    num_days = len(dates)
    num_employees = len(employees)

    fig, ax = plt.subplots(figsize=(num_days * 1.2, num_employees * 0.8))

    for i, job in enumerate(employeejobs):
        ax.axhspan(
            i,
            i + 1,
            xmin=0,
            xmax=-0.01,
            facecolor=job_colors.get(job, "white"),
            edgecolor="black",
            alpha=1,
        )

    for n_idx in range(num_employees):
        for d in range(num_days):
            shifts_today = [
                s
                for s in range(3)
                if schedule.get((n_idx, dates[d].isoformat(), s), False)
            ]
            if shifts_today:
                shift = shifts_today[0] if len(shifts_today) == 1 else None
                color = (
                    shift_colors.get(shift, "white") if shift is not None else "white"
                )
                ax.add_patch(plt.Rectangle((d, n_idx), 1, 1, color=color, ec="black"))
                symbol = shift_symbols.get(shift, "?")
                ax.text(
                    d + 0.5,
                    n_idx + 0.5,
                    symbol,
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                )
            else:
                ax.add_patch(plt.Rectangle((d, n_idx), 1, 1, color="white", ec="black"))

    ax.set_xlim(0, num_days)
    ax.set_ylim(0, num_employees)
    ax.set_xticks(np.arange(num_days) + 0.5)
    ax.set_yticks(np.arange(num_employees) + 0.5)

    # New Description Date
    date_labels = [dt.isoformat() for dt in dates]
    ax.set_xticklabels(
        date_labels,
        rotation=90,
        ha="center",
        va="center",
        fontsize=10,
    )
    ax.set_yticklabels(employeenames, fontsize=10)

    ax.invert_yaxis()
    ax.xaxis.tick_top()

    ax.set_xticks(np.arange(num_days), minor=True)
    ax.set_yticks(np.arange(num_employees), minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=0.5)

    # Create legends for job types and shift types
    job_patches = [
        mpatches.Patch(color=job_colors, label=job_name)
        for job_name, job_colors in job_colors.items()
    ]
    shift_patches = [
        mpatches.Patch(color=c, label=f"Shift {shift_symbols[s]}")
        for s, c in shift_colors.items()
    ]
    all_patches = job_patches + shift_patches

    ax.legend(
        handles=all_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.3),
        ncol=len(all_patches),
    )

    ax.set_title("Employee Scheduling Overview", pad=20)
    plt.tight_layout()
    plt.show()
