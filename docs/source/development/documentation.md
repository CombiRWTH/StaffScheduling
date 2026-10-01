# Maintaining documentation

Documentation changes accompany every implementation change. Update instructions and contracts when their behavior changes, and remove a limitation only after its acceptance check passes. Record the command, expected/actual result, revision and environment with the change.

## Reader goals and section ownership

The home page routes readers by purpose. Organize content by the question it answers, rather than by the legacy repositories or implementation ticket boundaries.

| Reader goal                              | Section            | Purpose                                                                     |
| ---------------------------------------- | ------------------ | --------------------------------------------------------------------------- |
| Try or install                           | `getting-started/` | One short launch path and complete machine prerequisites/configuration      |
| Complete a planning task                 | `user-guide/`      | Staff-admin actions, expected outcomes and recovery paths                   |
| Understand how it works                  | `architecture/`    | Responsibilities, data flow, domain, API, solver and adapter contracts      |
| Make a change                            | `development/`     | Commands, testing responsibilities and contribution procedures              |
| Assess correctness or reproduce a result | `validation/`      | Evidence/limitations, sourced reasoning, accepted examples and reproduction |

User-guide outlines are arranged in the planning task order, architecture follows the system boundaries, and validation separates reasoning from executed proof. The home page showcases only checked behavior and routes future example results to their evidence.

Use the terms in the root `GLOSSARY.md`; add a term there when one is resolved. Record a decision as a short ADR in `docs/adr/` only when it is hard to reverse, surprising without context and the result of a real trade-off. Keep installation in one place and link to it. Extend an existing page when it fits; add a page only when readers need a separate topic. Outline pages reserve sections without claiming that the feature works. Fill or reorganize them as verified behavior develops. Optional unsupported controls do not need a full guide.

## Evidence and accuracy

Quickstart liveness, offline tests, Linux-container checks, Linux-host checks and live database operations prove different things. Name the kind of evidence available. Source inspection establishes what a function defines; it does not establish that the external database or the complete UI flow works. Reference pages describe inspected source; user instructions require executed behavior checks.

Do not restore legacy commands or formats without checking them against the current code. Keep credentials, employee data and private operational evidence out of documentation. When changing a contract, document units, identifiers, side effects, failure handling and compatibility limits.

## Build and routes

Edit `docs/source/`. Add or remove the corresponding entry in `docs/mkdocs.yml`; every published Markdown page belongs in navigation. Preserve established paths when practical and update inbound links when moving a page. Links between pages use paths relative to the source page, including `.md`; MkDocs builds the site routes. Check fragments as well as file targets. See the [MkDocs navigation configuration](https://www.mkdocs.org/user-guide/configuration/#nav) and [Material section indexes](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages) for the native routing settings.

Run `just docs-check` for a strict build and `just docs` to inspect navigation/search locally. Check README links separately because README is rendered by GitHub. Generated `docs/site/` remains untracked. Strict builds check documentation references, including missing heading anchors: `validation.links.anchors: warn` makes broken fragments fail the gate. README targets and external URLs still need separate checks. Builds do not execute setup commands or establish feature acceptance.

## Documentation dependencies

`docs/pyproject.toml` has two direct dependencies: MkDocs builds/serves/deploys the site, and Material supplies the configured theme, search presentation and code-copy controls. Their lock includes required transitive packages, including Markdown rendering, syntax highlighting and the `pymdownx` extensions used by code blocks and the architecture diagram. Search uses MkDocs' built-in plugin.

No API-importing documentation plugin, second frontend documentation project, include plugin or generated Python reference is needed. HTTP schemas come from the running API's OpenAPI page. Keep the independent docs lock frozen; do not remove required transitive packages by hand or add plugins for unused features.
