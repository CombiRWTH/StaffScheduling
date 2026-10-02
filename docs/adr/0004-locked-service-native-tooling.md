# Use locked, service-native tooling with exact pins

Each service uses the standard tools of its ecosystem, configured inside the service: uv with a frozen lock, Ruff, strict Pyright and pytest for `api/`; pnpm with a frozen lock, ESLint, Prettier, strict TypeScript, React Doctor and Playwright for `webapp/`. Documentation has its own uv lock under `docs/`, so MkDocs does not enter the API environment. Python, Node, pnpm, uv and the tool versions are pinned exactly and match in Docker, CI and Git hooks, so a check gives the same result everywhere. When upgrading, we choose the newest stable release rather than an older long-term-support line.

## Considered Options

- **Keep npm for the webapp.** Rejected in favour of pnpm, whose `pnpm import` carried over the existing npm resolution and which installs strictly from its own lock.
- **Bun as package manager.** Rejected: it adds a second JavaScript runtime to reason about, while Node remains what Next.js and the containers run.
- **A shared root version file.** Rejected: nothing reads it. The service manifests and version files are the only version authority.
- **Floating image tags and tool ranges.** Rejected: results would change without a commit.

## Consequences

Checks never update locks; an upgrade is a deliberate commit that changes the manifest, lock, Dockerfile, CI and hook pins together. See [checks and tooling](../source/development/checks.md) for the current pins.
