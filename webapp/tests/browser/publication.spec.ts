import { expect, test, type Page } from "@playwright/test";

// The offline API (api/tests/browser_server.py) publishes into an in-memory TimeOffice roster. June at
// Station North is accepted; Station South alone lacks trusted context, so its check is incomplete. Both
// stations together are accepted, but every roster write at Station South fails like a database error.

const API = "http://127.0.0.1:18080";
const card = (page: Page) => page.getByLabel("Veröffentlichung");

/** Generate June for one station and open its review; the station name tells the new job from the previous one. */
async function generate(page: Page, station: { id: string; name: string }) {
  await page.goto(`/generation?month=2026-06&stations=${station.id}`);
  await page.getByLabel("Maximale Laufzeit (Sekunden)").fill("30");
  await page.getByRole("button", { name: "Starten" }).click();
  const latest = page.getByLabel("Letzte Generierung");
  await expect(latest).toContainText(`Juni 2026 (01.06.2026–30.06.2026) · ${station.name}`);
  await expect(latest).toContainText("Abgeschlossen", { timeout: 20_000 });
  await page.getByRole("link", { name: "Dienstplan prüfen" }).click();
}

test("an accepted schedule is published and cleared only after confirming the named scope", async ({ page }) => {
  await generate(page, { id: "101", name: "Example Station North" });
  const publication = card(page);
  const count = Number(
    await page.getByLabel("Dienstplan zur Prüfung").locator('dt:text-is("Dienste") + dd').textContent(),
  );
  expect(count).toBeGreaterThan(0);

  await publication.getByRole("button", { name: "In TimeOffice veröffentlichen" }).click();
  await expect(publication.getByRole("group", { name: "In TimeOffice veröffentlichen", exact: true })).toContainText(
    `Die veröffentlichten Dienste von Example Station North im Juni 2026 werden durch die ${count} Dienste`,
  );
  await publication.getByRole("button", { name: "Abbrechen" }).click();
  await expect(publication.getByRole("status")).toHaveCount(0);

  await publication.getByRole("button", { name: "In TimeOffice veröffentlichen" }).click();
  await publication.getByRole("button", { name: "Veröffentlichen bestätigen" }).click();
  await expect(publication.getByRole("status")).toHaveText(
    `Veröffentlicht: ${count} Dienste geschrieben und gelesen, 0 bisherige ersetzt.`,
  );

  const clear = publication.getByRole("group", { name: "Veröffentlichte Dienste entfernen", exact: true });
  // A cancelled clear removes nothing: the confirmed one afterwards still finds every published duty.
  await publication.getByRole("button", { name: "Veröffentlichte Dienste entfernen" }).click();
  await expect(clear.getByRole("group")).toContainText(
    "Alle veröffentlichten Dienste von Example Station North im Juni 2026 werden aus TimeOffice entfernt.",
  );
  await publication.getByRole("button", { name: "Abbrechen" }).click();
  await publication.getByRole("button", { name: "Veröffentlichte Dienste entfernen" }).click();
  await publication.getByRole("button", { name: "Entfernen bestätigen" }).click();
  await expect(clear.getByRole("status")).toHaveText(`Entfernt: ${count} veröffentlichte Dienste.`);
});

test("a schedule replaced after loading the page is refused, not published", async ({ page }) => {
  await page.goto("/review?month=2026-06&stations=101");
  const publication = card(page);
  await publication.getByRole("button", { name: "In TimeOffice veröffentlichen" }).click();

  // Another tab generates again, so the reviewed schedule is no longer the one on this page.
  const body = { planning_unit_ids: [101], planning_month: { year: 2026, month: 6 }, timeout_seconds: 30 };
  expect((await page.request.post(`${API}/generation`, { data: body })).status()).toBe(202);
  await expect
    .poll(async () => (await (await page.request.get(`${API}/generation`)).json()).state, { timeout: 20_000 })
    .toBe("completed");

  await publication.getByRole("button", { name: "Veröffentlichen bestätigen" }).click();
  await expect(publication.getByRole("alert")).toHaveText(
    "Der Dienstplan zur Prüfung hat sich geändert. Seite neu laden und erneut prüfen.",
  );
  await expect(publication.getByRole("status")).toHaveCount(0);
});

test("a failed publication says nothing changed, and nothing did", async ({ page }) => {
  await generate(page, { id: "101,102", name: "Example Station North, Example Station South" });
  const publication = card(page);
  await publication.getByRole("button", { name: "In TimeOffice veröffentlichen" }).click();
  await publication.getByRole("button", { name: "Veröffentlichen bestätigen" }).click();
  await expect(publication.getByRole("alert")).toHaveText(
    "TimeOffice-Abfrage fehlgeschlagen. Datenbankschema und Berechtigungen prüfen. Nichts wurde geändert.",
  );
  await expect(publication.getByRole("status")).toHaveCount(0);

  // The rolled-back write left no duty of either station to clear.
  const clear = publication.getByRole("group", { name: "Veröffentlichte Dienste entfernen", exact: true });
  await clear.getByRole("button", { name: "Veröffentlichte Dienste entfernen" }).click();
  await clear.getByRole("button", { name: "Entfernen bestätigen" }).click();
  await expect(clear.getByRole("status")).toHaveText("Entfernt: 0 veröffentlichte Dienste.");
});

test("a schedule the check did not accept cannot be published", async ({ page }) => {
  await generate(page, { id: "102", name: "Example Station South" });
  await expect(page.getByLabel("Dienstplan zur Prüfung")).toContainText("Unvollständig");
  const publication = card(page);
  await expect(publication).toContainText("Nur ein angenommener Dienstplan kann veröffentlicht werden.");
  await expect(publication.getByRole("button", { name: "In TimeOffice veröffentlichen" })).toHaveCount(0);
  await expect(publication.getByRole("button", { name: "Veröffentlichte Dienste entfernen" })).toBeVisible();
});
