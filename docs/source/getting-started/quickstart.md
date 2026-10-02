# Quickstart

You need [Docker with Compose](https://docs.docker.com/compose/install/), [just](https://github.com/casey/just#installation), a copy of this repository and the supplied test database password. Start Docker. No host Python, Node or pnpm installation is needed. On Windows, run the commands in Git Bash or WSL, not in the Command Prompt or PowerShell; see [prerequisites](installation.md#prerequisites).

## 1. Get the project

Download and extract the repository, or clone it with Git:

```sh
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
```

Use the supplied checkout if you already have one. Run the following commands from its root, where `compose.yaml` lives.

## 2. Place the password

The repository root contains an empty `.secrets` directory. Create a plain-text file named `db_password` inside it using your editor or file manager. Put only the supplied password in this plain-text file, without quotes. Keep it private and restrict file access to your user. Existing password files can be reused.

```text
StaffScheduling/
├── compose.yaml
├── .env                    # supplied non-secret database settings
└── .secrets/
    └── db_password         # supplied password; ignored by Git
```

If no password is available, leave the file empty: both services can start, while database operations report an unavailable integration.

The committed `.env` already contains the test database server, database name and user. [Installation](installation.md#database-configuration) explains how to use a different authorized database.

## 3. Start both services

```sh
just run
```

It builds and starts both services in the background and waits for their health checks; the first build downloads dependencies. It first runs [`just precheck`](installation.md#prerequisites), which stops if the password file is missing.

Open the webapp at <http://localhost:3000>. The API's interactive reference is at <http://localhost:8000/docs>; <http://localhost:8000/status> should return `{"status":"healthy"}`.

Open <http://localhost:3000/api/health> to check a real request from the webapp server to the API. It returns `503` if the API is unavailable. A healthy service does not prove database connectivity. Employee/configuration queries and generation need access to the TimeOffice network and database. Read [current limitations](../validation/index.md) before relying on planning or publication results.

## Stop or inspect

```sh
just logs
just stop
```

Stopping preserves files in `data/` and the dependency/build volumes. If startup fails, follow [troubleshooting](installation.md#troubleshooting).
