import { expect, test, type Page } from "@playwright/test";

// The offline API (api/tests/browser_server.py) has saved staffing for Station North in June,
// July and August, none in September. June solves for real for at most three seconds; July fails
// at runtime and August is infeasible, each after a two-second run. Jobs live in that process only.

const latest = (page: Page) => page.getByLabel("Letzte Generierung");

async function start(page: Page, url: string, seconds = "30") {
  await page.goto(url);
  await page.getByLabel("Maximale Laufzeit (Sekunden)").fill(seconds);
  await page.getByRole("button", { name: "Starten" }).click();
}

test("no result before the first run; incomplete or invalid input starts nothing", async ({ page }) => {
  await page.goto("/generation?month=2026-09&stations=101");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Dienstplan erstellen");
  await expect(page.getByText("September 2026 (01.09.2026–30.09.2026)")).toBeVisible();
  await expect(page.getByText("Example Station North", { exact: true }).last()).toBeVisible();
  await expect(page.getByText(/Kein Ergebnis verfügbar/)).toBeVisible();

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

test("a running job survives navigation, rejects a second run and ends as an unchecked draft", async ({
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
  await expect(latest(page)).toContainText(/Lösung|Keine Lösung/);
  await expect(latest(page)).toContainText("Noch nicht verfügbar");
  await expect(latest(page)).toContainText("nicht automatisch veröffentlicht");
  await expect(page.getByRole("button", { name: "Starten" })).toBeEnabled();
});

test("infeasible and failed runs are reported differently", async ({ page }) => {
  await start(page, "/generation?month=2026-08&stations=101");
  await expect(latest(page)).toContainText("Abgeschlossen", { timeout: 15_000 });
  await expect(latest(page)).toContainText("Keine Lösung möglich");

  await start(page, "/generation?month=2026-07&stations=101");
  await expect(latest(page)).toContainText("Fehlgeschlagen", { timeout: 15_000 });
  await expect(latest(page)).toContainText("Unerwarteter Fehler bei der Generierung");
  await expect(latest(page)).toContainText("Kein Ergebnis");
  await expect(latest(page)).not.toContainText("Fictional solver crash");
});
