import { expect, test, type Page } from "@playwright/test";

// The offline API (api/tests/browser_server.py) has saved staffing for Station North in June,
// July and August, none in September. June and August solve for real for at most three seconds;
// July fails at runtime and August's accounts are unreachable, each after a two-second run. Jobs live
// in that process only.

const latest = (page: Page) => page.getByLabel("Letzte Generierung");

async function start(page: Page, url: string, seconds = "30") {
  await page.goto(url);
  await page.getByLabel("Maximale Laufzeit").fill(seconds);
  await page.getByRole("button", { name: "Starten" }).click();
}

test("no result before the first run; incomplete or invalid input starts nothing", async ({ page }) => {
  await page.goto("/generation?month=2026-09&stations=101");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Dienstplan erstellen");
  const next = page.getByLabel("Neue Generierung");
  await expect(next.getByRole("heading")).toHaveText("September 2026 · Example Station North");
  await expect(next).toContainText("Ganzer Monat, 01.09.2026–30.09.2026");
  await expect(page.getByText(/Kein Ergebnis verfügbar/)).toBeVisible();
  // What a run reads and what it ignores are two separate lists.
  await expect(page.getByRole("list", { name: "Berücksichtigt" }).getByRole("listitem")).toContainText([
    "Wünsche",
    "Mindestbesetzung",
  ]);
  await expect(page.getByRole("list", { name: "Nicht berücksichtigt" }).getByRole("listitem")).toHaveText([
    "bestehende Dienste im Dienstplan",
  ]);

  await start(page, "/generation?month=2026-09&stations=101");
  await expect(page.getByText(/Mindestbesetzung jeder Station speichern.*keine Generierung gestartet/)).toBeVisible();
  await expect(page.getByText(/Kein Ergebnis verfügbar/)).toBeVisible();

  // A time limit below the minimum reaches the backend, which rejects it before any job exists.
  await start(page, "/generation?month=2026-06&stations=101", "10");
  await expect(page.getByText(/Generierung ungültig.*keine Generierung gestartet/)).toBeVisible();
  await expect(page.getByText(/Kein Ergebnis verfügbar/)).toBeVisible();

  await page.goto("/generation?month=2026-09");
  await expect(page.getByRole("button", { name: "Starten" })).toBeDisabled();
});

test("a running job survives navigation, rejects a second run and ends with its schedule check", async ({
  page,
  context,
}) => {
  const other = await context.newPage();
  await other.goto("/generation?month=2026-06&stations=101");

  await start(page, "/generation?month=2026-06&stations=101");
  await expect(latest(page)).toContainText("Läuft");
  await expect(latest(page)).toContainText("Juni 2026 (01.06.2026–30.06.2026) · Example Station North");
  await expect(page.getByRole("button", { name: "Starten" })).toBeDisabled();

  // The page loaded before the run still offers the button; the backend refuses the overlap.
  await other.getByRole("button", { name: "Starten" }).click();
  await expect(other.getByText(/Es läuft bereits eine Generierung/)).toBeVisible();

  await page.getByRole("link", { name: "Mitarbeiter" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mitarbeiter");
  await page.getByRole("link", { name: "Erstellen" }).click();
  await expect(latest(page)).toContainText("Abgeschlossen", { timeout: 20_000 });
  await expect(latest(page)).toContainText(/Optimale Lösung|Lösung gefunden/);
  // The independent check accepts the plan; the headline says what to do next.
  await expect(latest(page)).toContainText("Dienstplan erstellt, Regeln eingehalten");
  await expect(latest(page)).toContainText("nicht automatisch veröffentlicht");
  // June 5 needs one professional more than the station has: the hint explains the gap.
  await expect(latest(page).getByText("Hinweise", { exact: true })).toBeVisible();
  await expect(latest(page)).toContainText(
    "Für 1 Schicht gibt es zu wenige einsetzbare Mitarbeiter; sie bleiben als Lücken offen",
  );
  // What lies beyond the month is technical detail, opened by keyboard.
  await latest(page).getByText("Technische Details").press("Enter");
  await expect(latest(page).getByText("Über den Monat hinaus, hier nicht bewertet")).toBeVisible();
  await expect(latest(page).getByText(/^Freie Sonntage im Jahr 01\.01\.2026–31\.12\.2026$/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Starten" })).toBeEnabled();
});

test("infeasible and failed runs are reported differently", async ({ page }) => {
  await start(page, "/generation?month=2026-08&stations=101");
  await expect(latest(page)).toContainText("Abgeschlossen", { timeout: 15_000 });
  await expect(latest(page)).toContainText("Keine Lösung möglich");
  await expect(latest(page)).toContainText("Kein Plan zu prüfen");
  // The hints name the demand no employee can cover, for staff admins and developers alike.
  await expect(latest(page).getByText("Hinweise", { exact: true })).toBeVisible();
  await expect(latest(page)).toContainText("Mindestbesetzung nicht erreichbar: Für 2 Schichten");
  await expect(latest(page)).toContainText("Monatskonto nicht erreichbar: 2 Mitarbeiter");
  // The solver's own English messages stay in the technical details for developers.
  await expect(
    latest(page)
      .getByText(/can work it/)
      .first(),
  ).toBeHidden();
  await latest(page).getByText("Technische Details").click();
  await expect(
    latest(page)
      .getByText(/can work it/)
      .first(),
  ).toBeVisible();
  await expect(latest(page).getByRole("link", { name: "Dienstplan prüfen" })).toHaveCount(0);

  await start(page, "/generation?month=2026-07&stations=101");
  await expect(latest(page)).toContainText("Fehlgeschlagen", { timeout: 15_000 });
  await expect(latest(page)).toContainText("Unerwarteter Fehler bei der Generierung");
  await expect(latest(page)).toContainText("Kein Ergebnis");
  // The backend keeps internal error text in its log; not even the technical details show it.
  await latest(page).getByText("Technische Details").click();
  await expect(latest(page)).not.toContainText("Fictional solver crash");
});
