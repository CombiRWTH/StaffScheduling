# Troubleshooting

Follow [installation and connection failures](../installation.md#start-with-docker) first. Check API `/status` and the webapp server's `SOLVER_API_URL` independently of SQL Server access.

For case files, use the default root `data/cases/` directory or set the server-side `CASES_DIR` environment variable. API files and outputs remain separate. Restart Next.js after changing environment variables.

A missing route or inconsistent generation/progress result may be a [known integration gap](solver-integration.md). The frontend's existing TypeScript failure and solver test failure are recorded in [migration verification](../developer-view/monorepo-migration.md).

The [historical troubleshooting reference](../collection-of-old-docs/webapp/troubleshooting.md) preserves old diagnostics. Its independent installer, auto-start and CLI instructions are retired; they do not describe this monorepo's setup.
