# Quickstart

You need [Docker with Compose](https://docs.docker.com/compose/install/), a copy of this repository and the supplied test database password. Start Docker. No host Python, Node, pnpm or just installation is needed.

## 1. Get the project

Download and extract the repository, or clone it with Git:

```sh
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
```

Use the supplied checkout if you already have one. Run the following commands from its root, where `compose.yaml` lives.

## 2. Place the password

Create a `.secrets` directory in the repository root, then create a plain-text file named `db_password` inside it using your editor or file manager. Put only the supplied password in this plain-text file, without quotes. Keep it private and restrict file access to your user. Existing password files can be reused.

```text
StaffScheduling/
├── compose.yaml
├── .env                    # supplied non-secret database settings
└── .secrets/
    └── db_password         # supplied password; ignored by Git
```

The committed `.env` already contains the test database server, database name and user. [Installation](installation.md#database-configuration) explains how to use a different authorized database.

## 3. Start both services

```sh
docker compose up --build --wait
```

The first build downloads dependencies. This command runs in the background and waits for the service health checks, as described in the [Compose command reference](https://docs.docker.com/reference/cli/docker/compose/up/).

Open the webapp at <http://localhost:3000>. The API's interactive reference is at <http://localhost:8000/docs>; <http://localhost:8000/status> should return `{"status":"healthy"}`.

A healthy service does not prove database connectivity. Employee/configuration queries and generation need access to the TimeOffice network and database. Read [current limitations](../validation/index.md) before relying on planning or publication results.

## Stop or inspect

```sh
docker compose ps
docker compose logs --follow
docker compose down
```

Stopping preserves files in `data/` and the dependency/build volumes. If startup fails, follow [troubleshooting](installation.md#troubleshooting). If just is already installed, `just run`, `just logs` and `just stop` wrap these same Compose operations.
