# Web Interface (StaffSchedulingWeb)

In addition to the CLI and the FastAPI-based HTTP interface, a full-featured **web application** is available that provides a modern, browser-based frontend for the Staff Scheduling solver. The project is called **StaffSchedulingWeb** and is maintained in a [separate repository](https://github.com/julian466/StaffSchedulingWeb).

!!! info "Dedicated Documentation"
    StaffSchedulingWeb has its own comprehensive documentation covering installation, usage, architecture, and development.
    **[View the StaffSchedulingWeb Documentation →](https://julian466.github.io/StaffSchedulingWeb/)**

## Overview

StaffSchedulingWeb is a [Next.js](https://nextjs.org/) application (App Router) that wraps around the StaffScheduling solver API. It allows users to configure, run, and inspect scheduling solutions entirely through the browser — no command-line interaction required.

### Key Features

| Area | Capabilities |
|---|---|
| **Data Management** | Import/export JSON case files, manage employees, shifts, vacations, forbidden days, and qualification mappings |
| **Solver Control** | Trigger single or multi-solve runs, monitor progress in real time via status polling, adjust solver timeout |
| **Solution Inspection** | Interactive schedule grid, per-employee statistics, constraint violation highlights, compare multiple solutions side-by-side |
| **TimeOffice Integration** | Fetch planning data from and insert solutions back into the TimeOffice database |
| **Configuration** | Full UI for all solver settings — weights, round permissions, minimum staffing levels, blocked/planned shifts |

### Architecture at a Glance

```
┌──────────────────────────────┐       HTTP / JSON        ┌──────────────────────────┐
│   StaffSchedulingWeb         │  ◄──────────────────────► │   StaffScheduling API    │
│   (Next.js Frontend)         │    /solve, /status, ...   │   (FastAPI Backend)      │
│   Port 3000                  │                           │   Port 8000              │
└──────────────────────────────┘                           └──────────────────────────┘
```

The frontend communicates exclusively through the REST endpoints documented in the [API section](./api.md). No direct database access is required from the web application — all database operations (fetch, insert, delete) are handled by the backend API.

### Technology Stack

- **Framework:** Next.js 16 (App Router, React 19, TypeScript)
- **UI Components:** shadcn/ui + Tailwind CSS
- **State Management:** React Context + custom hooks
- **Data Persistence:** LowDB (lightweight JSON file storage for case data)
- **Architecture:** Clean Architecture (Controllers → Use Cases → Repositories)

## Getting Started

To set up and run StaffSchedulingWeb alongside the solver backend:

1. **Start the solver API** (this project):
    ```bash
    uv run staff-scheduling-api
    ```

2. **Clone and start the web application:**
    ```bash
    git clone https://github.com/julian466/StaffSchedulingWeb.git
    cd StaffSchedulingWeb
    npm install
    npm run dev
    ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

For detailed setup instructions, configuration options, and development guides, refer to the [StaffSchedulingWeb Documentation](https://julian466.github.io/StaffSchedulingWeb/).

## Relation to the Legacy Web Interface

The original `src/web/` directory in this repository contains a minimal Flask-based visualization tool (`app.py`) that was used during early development. **StaffSchedulingWeb replaces and significantly extends this legacy interface** with a production-ready frontend covering the full scheduling workflow — from data import through solver execution to solution inspection and TimeOffice write-back.
