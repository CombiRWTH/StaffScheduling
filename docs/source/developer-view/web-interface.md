# Web interface

The Next.js webapp lives in `webapp/` in this repository. See the shared [installation guide](../installation.md), [workflow](../webapp/user-guide.md), [developer reference](../webapp/developer-guide.md), and [integration limits](../webapp/solver-integration.md).

Next.js pages, components, features, configuration and imported implementation layers share one `webapp/src/` root. Server-side API calls use `SOLVER_API_URL`; browser interactions go through Next.js pages, server actions and routes. The default configuration selects API mode and keeps Python auto-start disabled.

The imported UI temporarily retains its file schemas under root `data/cases/`; the obsolete CLI adapter and bundled case directories have been removed. Endpoint and model reconciliation happen in subsequent feature slices. Existing views and screenshots do not imply that fetch/generate/publish operations work end to end.
