# Selection and employee inspection

The selection and read-only employee view use the canonical API. The automated [browser procedure](../development/testing.md#staff-admin-browser-flows) passes with fictional SQL results through the real Next.js/FastAPI read path. Live TimeOffice data acceptance remains outstanding; see [limitations](../validation/index.md).

Return to the [documentation overview](index.md).

## Select month and planning units

1. Start both services as described in [installation](../getting-started/installation.md), then open <http://localhost:3000>.
2. Choose **Planungsmonat**, exactly one full calendar month. The station list is loaded from the backend for that month, using actual display names. A station requires exactly one configured monthly target plan; plan/status IDs stay inside the adapter.
3. Select one or more **Stationen**, then open **Mitarbeiter**. The URL carries `month=YYYY-MM&stations=ID,ID`; the selection is retained across navigation. A pool is context, never a selectable demand destination.
4. Use **Stationen aktualisieren** to reload options and the current page. On a month change, still-available stations remain selected; stations without a target in the new month are removed.

Changing month/stations replaces the displayed inspection, including filters/details. While the next inspection loads, a loading message replaces the old table. No local case files or successful old-scope results substitute for unavailable source data. Employee inspection is independent of the retired workflow's case lock.

## Inspect employees and memberships

The heading names the selected stations and inclusive month dates. **Pool-Kontext** names pools discovered from the dated home memberships of station-eligible employees. Their other pool employees are included for inspection, even if they have no membership permitting an assignment at the selected stations. No home relationship means no inferred pool association.

Each employee appears once by stable positive ID. Display names may change without changing identity. Search by name, ID, qualification or unit name; **Einheit** filters employees by membership. Open **Details** for all dated memberships, including home/replacement flags and membership qualifications. Professional, assistant, trainee and MFA remain distinct. Employee-level qualification does not override a different unit membership qualification.

**Heimat: ja** identifies origin; a dated station membership identifies destination eligibility. Pool membership alone grants no station eligibility. Ambiguous or missing home origin for an active membership is an input error, not a guessed jumper classification. Special capabilities are absent from this inspection response.

## Inspect existing work and availability

Details show monthly target minutes, available actual minutes, verified credit totals/items and their evidence source. A source actual total is displayed separately and is never treated as approved credit. Zero is displayed only when explicitly supplied; absent actual totals show **nicht verfügbar**. Every participant requires a target account and a prepared declaration of complete monthly credits and additional hard restrictions.

Credits list full dates, minute amounts, approved-absence/trusted-work kind and provenance. Native dated absences and prepared additional hard restrictions are shown separately from soft wishes, with reasons, sources and allowed-shift IDs where applicable. Explicit empty arrays produce **Explizit keine…**, not an inferred default. This view does not prorate targets, calculate a candidate's balance, edit employees or run generation.

Connected prerequisites include read access to the configured TimeOffice tables and explicitly prepared [employee/month evidence](../architecture/timeoffice.md#employee-inspection-evidence). Missing setup/data must be corrected by the authorized database preparer; refreshing cannot create it.

## Empty inputs and unavailable data

- Without a month/station selection, the page requests a selection.
- A month without target stations reports no available stations. A complete selected scope without members reports no employees. An empty search/filter result is distinct from an empty scope.
- Loading displays a status message. Incomplete targets, identities, memberships, account/credit/restriction evidence or duplicate source facts reject the complete inspection; no partial station table is displayed.
- Backend/TimeOffice failures show a connection/setup message. Verify configuration, network/VPN, TLS and read permissions using [installation](../getting-started/installation.md#database-configuration), then refresh options/reopen the employee page. Errors expose no raw SQL rows or connection secrets.

Recurring wishes/availability and all four template families remain discoverable as unsupported. Optimization is omitted from navigation. Saved library, monthly configuration, generation and review are not established by this slice.
