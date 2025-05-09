import json
import streamlit as st
import os
from vis import create_roster_table

st.set_page_config(
    layout="wide",
    page_title="Staff Scheduling Visualization",
    page_icon="📅",
)
st.title("📅 Staff Scheduling Visualization")

solution_files = [
    f
    for f in os.listdir("found_solutions")
    if os.path.isfile(os.path.join("found_solutions", f))
]

selected_file = st.selectbox("Select a solution", solution_files, index=1)

if selected_file:
    with open(os.path.join("found_solutions", selected_file), "r") as file:
        data = json.load(file)

    with st.expander("Open to see solution content"):
        st.json(data, expanded=False)

    solutions = data["solutions"]

    st.subheader("Metrics", divider=True)
    st.metric("Solutions", value=len(solutions), border=True)

    employees = data["employees"]
    num_days = max(int(k.split(",")[1]) for sol in solutions for k in sol.keys()) + 1
    for i, solution in enumerate(data["solutions"]):
        st.subheader(f"Solution #{i + 1}", divider=True)
        image_buffer = create_roster_table(solution, employees, num_days)
        st.image(image_buffer)
