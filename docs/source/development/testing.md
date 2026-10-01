# Testing

Run commands from the repository root after the [native tool installation](../getting-started/installation.md#optional-native-developer-setup). Docker is also needed for the isolated foundation smoke. [Current limitations](../validation/index.md) records failing gates.

## Unit responsibilities

`just test` runs the offline API suite, including tests marked `integration`; only explicitly external `timeoffice` tests are excluded by default. Solver constraint/objective tests own local rules. Settings tests own secret loading. The foundation tests exercise API liveness without credentials, shared database error sanitization/TLS, driver/settings validation and diagnostic cleanup/read-only query behavior.

## Service and adapter integration

```sh
just smoke
```

The smoke builds and boots both development images with fake localhost database settings, an empty temporary secret file, a unique project, dynamically allocated loopback ports and temporary output directories. It verifies API liveness, an actual request through the Next `/api/health` handler, an actionable unavailable-database `503`, unavailable-API `503`, recovery, and host/container output readability after stop/recreation. Cleanup removes only its own containers, network, volumes and temporary data; failures produce logs and a nonzero exit. It uses Docker, curl and a POSIX shell, without host Python or Node. It also calls both published host ports. A failed smoke must not be treated as accepted startup.

FastAPI and Next source reload were checked separately with isolated source copies: editing each live bind mount changed its HTTP response without rebuilding. Host `.venv`, `node_modules`, `.next`, local environment files and secrets are excluded from image build contexts; container dependency/build volumes mask host directories.

## Staff-admin browser flows

The five core staff-admin system flow families remain pending canonical feature work. The foundation smoke is an HTTP/system-boundary check, not browser or schedule acceptance.

## Live TimeOffice verification

With services running, `just connectivity` performs only configuration/ODBC/DNS/login/`SELECT 1` checks. It needs the authorized connection settings, private password and VPN/network/TLS prerequisites documented in [installation](../getting-started/installation.md#database-configuration). It never calls domain readers, which may provision supplemental tables. A successful diagnostic would prove basic connection/query access, not planning-table permissions or valid scheduling data.

`just test-timeoffice` runs only explicitly external tests. No such tests are present yet: pytest exits with status 5, which is a missing gate, not success. Later live checks must use a declared prepared test database, serialize writes and independently verify publication/recovery scope.

## Linux and clean-checkout checks

The foundation was built and exercised in Docker Desktop Linux arm64 containers on macOS, including ODBC Driver 18 imports, HTTP connectivity, reload and persistent outputs. A Linux amd64 API image also passed build/import/ODBC checks. These are container/platform checks, not an actual Linux-host run. Hosted CI and the prepared laptop's Linux startup, output permissions, VPN/firewall and live database acceptance remain final verification gates.

CI's container job invokes the same credential-free `just smoke`; its independent jobs still report existing type/build and solver failures. To repeat foundation verification on a Linux host, frozen-install native tools, run `just check`, retain every failing result, and run the read-only diagnostic separately with authorized configuration. The production webapp build and the final clean-checkout system/data checks remain separate acceptance evidence.
