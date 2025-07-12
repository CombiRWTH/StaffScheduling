# Staff Scheduling Optimization in Hospitals

Welcome to the Staff Scheduling Optimization project repository! This project was developed by students from the Chair of Combinatorial Optimization at RWTH Aachen University in collaboration with St. Marien-Hospital Düren and Pradtke GmbH.

The primary aim of this project is to automate the existing scheduling process within hospitals using TimeOffice software, a widely adopted tool for schedule creation. Currently, the creation of staff schedules is often still managed manually by the station management, which is time-consuming due to the surprisingly complex nature of meeting all necessary constraints.
Our approach involved automatically extracting data from the TimeOffice application, approximating an optimal staff schedule that meets all necessary constraints, and integrating this plan back into the TimeOffice system.

For detailed information about our methodology, results, and how to use the provided resources, please refer to the documentation included in this repository.

## Documentation

To explore the documentation, you can either view it online or run it locally.
- **Online Documentation 🌐**

  You can view the online documentation [here](https://combirwth.github.io/StaffScheduling/).

- **Local Documentation 📚**

  ```shell
  uv sync --extra docs
  uv run mkdocs serve
  ```
  Keep in mind to check the [pre-requisites](https://combirwth.github.io/StaffScheduling/getting-started/prerequisites) for the project before running the documentation locally.
