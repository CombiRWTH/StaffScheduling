import matplotlib.pyplot as plt

# Sample simplified data (you should replace with full data input)
data = {
    "employees": {
        "name_to_index": {"Pauline": 0, "Jonas": 1, "Marie": 2},
        "name_to_qualification": {
            "Pauline": "Azubi",
            "Jonas": "Azubi",
            "Marie": "Azubi",
        },
    },
    "constraints": {"Target Working Hours": {"shift_idx_to_min": [600, 700, 500]}},
    "solutions": [
        {
            "(0, 0, 0)": 1,
            "(0, 1, 1)": 0,
            "(1, 0, 2)": 1,
            "(1, 1, 0)": 1,
            "(2, 0, 0)": 1,
            "(2, 1, 2)": 1,
        }
    ],
}

# Extract info
employees = list(data["employees"]["name_to_index"].keys())
name_to_index = data["employees"]["name_to_index"]
qualifications = data["employees"]["name_to_qualification"]
shift_minutes = data["constraints"]["Target Working Hours"]["shift_idx_to_min"]
solution = data["solutions"][0]

num_days = max(int(k.split(",")[1]) for k in solution.keys()) + 1
num_employees = len(employees)

# Define color maps
qual_color = {
    "Azubi": "#ADD8E6",  # light blue
    "Fachkraft": "#90EE90",  # light green
    "Praktikant": "#D3D3D3",  # light gray
}
shift_code = {0: "E", 1: "L", 2: "N"}
shift_color = {"E": "yellow", "L": "skyblue", "N": "black"}

# Create table data
cell_text = []
cell_colors = []
hours_column = []

for name in employees:
    idx = name_to_index[name]
    qual = qualifications[name]
    row = []
    colors = []

    total_minutes = 0

    # Employee cell
    row.append(f"{name}\n({qual})")
    colors.append(qual_color.get(qual, "white"))

    for day in range(num_days):
        shift_char = ""
        color = "white"
        text_color = "black"
        for s in range(3):
            key = f"({idx}, {day}, {s})"
            if solution.get(key, 0) == 1:
                shift_char = shift_code[s]
                color = shift_color[shift_char]
                if shift_char == "N":
                    text_color = "white"
                total_minutes += shift_minutes[s]
                break

        row.append(shift_char)
        colors.append(color)

    row.append(str(total_minutes))
    colors.append("lightgray")

    cell_text.append(row)
    cell_colors.append(colors)

# Table column labels
columns = ["Employee"] + [f"D{d}" for d in range(num_days)] + ["Total Min"]

fig, ax = plt.subplots(figsize=(0.6 * len(columns), 0.5 * len(employees)))
table = ax.table(
    cellText=cell_text,
    colLabels=columns,
    cellColours=cell_colors,
    loc="center",
    cellLoc="center",
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.2)

# Style adjustments
for key, cell in table.get_celld().items():
    row, col = key
    if row == 0:
        cell.set_text_props(weight="bold", color="black")
    elif col == 0:
        cell.set_text_props(fontsize=9)
    if row > 0 and col > 0:
        if cell.get_text().get_text() == "N":
            cell.get_text().set_color("white")

ax.axis("off")
plt.tight_layout()
plt.show()
