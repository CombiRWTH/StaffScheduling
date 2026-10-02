# Backup plans

A fallback dataset from an earlier project state, kept as a backup. It is superseded by the plans in `plaene/`.

- Stations 77 and 78, January–June 2026: one `<MM>_2026_dienstplan.json` per station and month, plus `combined_77_78_dienstplan.json`.
- The format predates the current bundle format (it uses `rounds`, among other differences). The application and its tests do not read these files, and no generation uses them as input.
