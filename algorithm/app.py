import streamlit as st
import matplotlib.pyplot as plt
import io
import json


SOLUTION_FILENAME = "solutions_2025-05-06_09-21-49.json"


# ===== Load your JSON data (replace this with your real JSON load) =====

with open(f"found_solutions/{SOLUTION_FILENAME}", "r") as f:
    data = json.load(f)

employees = list(data["employees"]["name_to_index"].keys())
name_to_index = data["employees"]["name_to_index"]
# qualifications = data["employees"]["name_to_qualification"]
# shift_minutes = data["constraints"]["Target Working Hours"]["shift_idx_to_min"]
solutions = data["solutions"]

num_days = max(int(k.split(",")[1]) for sol in solutions for k in sol.keys()) + 1

# free_days = {}
# free_shifts = {}

# for entry in data["constraints"]["Free Shifts and Vacation Days"]["days_off"]:
#     name = entry["name"]
#     free_days[name] = set(entry["days"])

# for entry in data["constraints"]["Free Shifts and Vacation Days"]["shifts_off"]:
#     name = entry["name"]
#     for day, shift in entry["shifts"]:
#         free_shifts.setdefault(name, {}).setdefault(day, set()).add(shift)


# ===== Create duty roster figure =====
def create_roster_table(solution):
    shift_code = {0: "E", 1: "L", 2: "N"}
    shift_color = {"E": "yellow", "L": "skyblue", "N": "black"}
    qual_color = {
        "Azubi": "#ADD8E6",
        "Fachkraft": "#90EE90",
        "Praktikant": "#D3D3D3",
        "Unknown": "#ADD8E6",
    }

    MAX_NAME_LENGTH = 16  # You can tweak this
    PLACEHOLDER = "..."
    ROW_HEIGHT = 0.06  # Adjust for your preference
    CELL_WIDTH = 0.04

    cell_text = []
    cell_colors = []
    cell_borders = []

    for name in employees:
        idx = name_to_index[name]
        # qual = qualifications[name]
        qual = "Unknown"

        if len(name) > MAX_NAME_LENGTH:
            short_name = name[: MAX_NAME_LENGTH - len(PLACEHOLDER)] + PLACEHOLDER
        else:
            short_name = name

        # Multiline name + qualification
        label = f"{short_name}\n({qual})"
        row = [label]
        colors = [qual_color.get(qual, "white")]
        borders = [None]  # first column

        # total_minutes = 0
        number_of_shifts = 0

        for day in range(num_days):
            shift_char = ""
            bg_color = "white"
            border_color = None
            border_width = 5  # visible edge

            for s in range(3):
                key = f"({idx}, {day}, {s})"
                if solution.get(key, 0) == 1:
                    shift_char = shift_code[s]
                    bg_color = (
                        "lightgray" if shift_char == "N" else shift_color[shift_char]
                    )
                    # total_minutes += shift_minutes[s]
                    number_of_shifts += 1
                    break

            # Free shift or day marking
            # if name in free_days and day in free_days[name]:
            #     border_color = "red"
            # elif name in free_shifts and day in free_shifts[name]:
            #     shifts = free_shifts[name][day]
            #     if 0 in shifts:
            #         border_color = "#d4a017"  # dark yellow
            #     elif 1 in shifts:
            #         border_color = "#1e90ff"  # darker blue
            #     elif 2 in shifts:
            #         border_color = "black"

            row.append(shift_char)
            colors.append(bg_color)
            borders.append((border_color, border_width) if border_color else None)

        # row.append(str(total_minutes))
        row.append(str(number_of_shifts))
        colors.append("lightgray")
        borders.append(None)  # total column

        cell_text.append(row)
        cell_colors.append(colors)
        cell_borders.append(borders)

    # columns = ["Employee"] + [f"D{d}" for d in range(num_days)] + ["Total Min"]
    columns = ["Employee"] + [f"D{d}" for d in range(num_days)] + ["Number of Shifts"]
    fig, ax = plt.subplots(
        figsize=(0.6 * len(columns), 0.4 * len(employees)), dpi=200
    )  # Increased DPI
    table = ax.table(
        cellText=cell_text,
        colLabels=columns,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )

    # Apply colored borders
    # Full border drawing (all 4 sides)
    for row_idx, borders in enumerate(cell_borders, start=1):  # skip header
        for col_idx, border in enumerate(borders):
            if border:
                border_color, border_width = border
                cell = table[row_idx, col_idx]

                cell.set_edgecolor(border_color)
                cell.set_linewidth(border_width)

    for (row, col), cell in table.get_celld().items():
        cell.set_height(ROW_HEIGHT)
        if col == 0:
            cell.set_width(0.1)  # wider for name+qualification
        else:
            cell.set_width(CELL_WIDTH)  # uniform small widths for day columns

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.1)

    for key, cell in table.get_celld().items():
        row, col = key
        if row == 0:
            cell.set_text_props(weight="bold", color="black")
        elif col == 0:
            cell.set_text_props(fontsize=9)
        if row > 0 and col > 0 and cell.get_text().get_text() == "N":
            cell.get_text().set_color("white")

    ax.axis("off")

    # Use BytesIO to render at full resolution
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    return buf


# ===== Streamlit UI =====
st.set_page_config(layout="wide", page_title="Duty Roaster Viewer")

st.title("📅 Duty Roaster Viewer")

for i, solution in enumerate(solutions):
    st.markdown(f"## Solution #{i + 1}")
    image_buffer = create_roster_table(solution)
    st.image(image_buffer)
