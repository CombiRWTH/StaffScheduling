import { expect, test, type Page } from "@playwright/test";

// The offline API keeps saved configuration in memory and fails every write for
// "Example Jumper Three" and "Example Station South" (see api/tests/browser_server.py).

async function choose(page: Page, label: string, option: string) {
  await page.getByRole("combobox", { name: label }).click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

const day = (page: Page, date: string) => page.getByRole("button", { name: date, exact: true });

test("edit, reload and delete availability, and keep wishes separate", async ({ page }) => {
  await page.goto("/availability?month=2026-01&stations=101,102");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Verfügbarkeit");
  await expect(page.getByRole("combobox", { name: "Mitarbeiter" })).toHaveText(/Example MFA One/);
  await expect(day(page, "01.01.2026")).toContainText("Urlaub · U");

  await day(page, "05.01.2026").click();
  await choose(page, "Art der Einschränkung", "Nur bestimmte Schichten");
  await page.getByRole("checkbox", { name: "F" }).click();
  await page.getByRole("checkbox", { name: "S" }).click();
  await page.getByLabel("Grund").fill("Arzttermin");
  await page.getByRole("button", { name: "Einschränkung speichern" }).click();
  await expect(page.getByRole("status")).toHaveText("Einschränkung gespeichert.");
  await expect(day(page, "05.01.2026")).toContainText("Nur bestimmte Schichten · F, S · Arzttermin");

  await page.reload();
  await expect(day(page, "05.01.2026")).toContainText("Nur bestimmte Schichten · F, S · Arzttermin");
  await day(page, "05.01.2026").click();
  await choose(page, "Art der Einschränkung", "Urlaub");
  await page.getByRole("button", { name: "Einschränkung speichern" }).click();
  await expect(day(page, "05.01.2026")).toContainText("Urlaub · Arzttermin");
  await expect(day(page, "01.01.2026")).toContainText("Urlaub · U");

  await expect(page.getByText(/bei der Dienstplanerstellung derzeit nicht berücksichtigt/)).toBeVisible();
  await choose(page, "Art des Wunsches", "Freier Tag");
  await page.getByRole("button", { name: "Wunsch speichern" }).click();
  await expect(day(page, "05.01.2026")).toContainText("Freier Tag");
  await page.getByRole("button", { name: "Wunsch entfernen" }).click();
  await expect(day(page, "05.01.2026")).not.toContainText("Freier Tag");
  await expect(day(page, "05.01.2026")).toContainText("Urlaub · Arzttermin");

  // The other direction: availability edits and deletes leave an existing wish alone.
  await choose(page, "Art des Wunsches", "Wunschtag");
  await page.getByRole("button", { name: "Wunsch speichern" }).click();
  await expect(day(page, "05.01.2026")).toContainText("Wunschtag");
  await choose(page, "Art der Einschränkung", "Fortbildung");
  await page.getByRole("button", { name: "Einschränkung speichern" }).click();
  await expect(day(page, "05.01.2026")).toContainText("Fortbildung · Arzttermin");
  await expect(day(page, "05.01.2026")).toContainText("Wunschtag");
  await page.getByRole("button", { name: "Einschränkung entfernen" }).click();
  await expect(day(page, "05.01.2026")).not.toContainText("Fortbildung");
  await expect(day(page, "05.01.2026")).toContainText("Wunschtag");
  await page.getByRole("button", { name: "Wunsch entfernen" }).click();
  await page.reload();
  await expect(day(page, "05.01.2026")).toHaveText("5");
  await expect(day(page, "01.01.2026")).toContainText("Neujahr");
});

test("a failed availability save keeps the entry and shows no success", async ({ page }) => {
  await page.goto("/availability?month=2026-01&stations=101,102");
  await choose(page, "Mitarbeiter", "3 · Example Jumper Three");
  await expect(page).toHaveURL(/employee=3/);
  await day(page, "06.01.2026").click();
  await choose(page, "Art der Einschränkung", "Fortbildung");
  await page.getByRole("button", { name: "Einschränkung speichern" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "nicht gespeichert" })).toBeVisible();
  await expect(page.getByRole("status")).toHaveCount(0);
  await expect(page.getByRole("combobox", { name: "Art der Einschränkung" })).toHaveText("Fortbildung");
  await expect(day(page, "06.01.2026")).toHaveText("6");
});

test("save and reload dated demand, reset edits and apply a previewed pattern", async ({ page }) => {
  await page.goto("/staffing?month=2026-01&stations=101,102");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mindestbesetzung");
  await expect(page.getByText("Für diesen Monat ist noch keine Mindestbesetzung gespeichert.")).toBeVisible();
  await expect(page.getByRole("row", { name: /01\.01\.2026/ }).first()).toContainText("Neujahr");
  const cell = (shift: string, date: string) => page.getByLabel(`${shift} am ${date}`, { exact: true });
  const changed = page.locator("input[data-changed]");

  await cell("F", "03.01.2026").fill("2");
  await expect(page.getByText("1 ungespeicherte Änderung")).toBeVisible();
  await expect(cell("F", "03.01.2026")).toHaveAccessibleDescription("Geändert, gespeichert: 0");
  await expect(page.getByRole("tab", { name: "Fachkraft (geändert)" })).toBeVisible();
  await page.getByRole("button", { name: "Zurücksetzen" }).click();
  await expect(cell("F", "03.01.2026")).toHaveValue("0");
  await expect(changed).toHaveCount(0);

  await cell("F", "03.01.2026").fill("2");
  await page.getByRole("tab", { name: "MFA" }).click();
  await cell("Z", "02.01.2026").fill("1");
  await expect(page.getByText("2 ungespeicherte Änderungen")).toBeVisible();
  await page.getByRole("button", { name: "Speichern" }).click();
  await expect(page.getByRole("status")).toHaveText("Mindestbesetzung gespeichert.");
  await expect(changed).toHaveCount(0);
  await expect(page.getByText(/ungespeicherte Änderung/)).toHaveCount(0);

  await page.reload();
  await expect(page.getByText("Für diesen Monat ist noch keine Mindestbesetzung gespeichert.")).toHaveCount(0);
  await expect(cell("F", "03.01.2026")).toHaveValue("2");
  await page.getByRole("tab", { name: "MFA" }).click();
  await expect(cell("Z", "02.01.2026")).toHaveValue("1");
  await expect(cell("Z", "03.01.2026")).toHaveValue("0");

  await page.getByRole("tab", { name: "Fachkraft" }).click();
  await page.getByText("Wochenmuster anwenden").press("Enter");
  await page.getByLabel("Muster F Mo", { exact: true }).fill("3");
  await page.getByLabel("Muster F Feiertag", { exact: true }).fill("1");
  await page.getByRole("button", { name: "Vorschau" }).click();
  // New Year's Day takes the holiday row; the saved Saturday value is replaced by the pattern's zero.
  await expect(page.getByRole("region", { name: "Vorschau" })).toContainText(
    "6 Tage werden ersetzt: 01.01., 03.01., 05.01., 12.01., 19.01., 26.01.",
  );
  await expect(cell("F", "05.01.2026")).toHaveValue("0");
  await page.getByRole("button", { name: "Übernehmen" }).click();
  await expect(cell("F", "05.01.2026")).toHaveValue("3");
  await expect(cell("F", "01.01.2026")).toHaveValue("1");
  await expect(cell("F", "03.01.2026")).toHaveValue("0");
  // Applied cells are marked like direct edits, also a saved count replaced by zero.
  await expect(changed).toHaveCount(6);
  await expect(cell("F", "03.01.2026")).toHaveAccessibleDescription("Geändert, gespeichert: 2");
  await expect(cell("F", "06.01.2026")).not.toHaveAttribute("data-changed");
  // Each qualification has its own pattern.
  await page.getByRole("tab", { name: "MFA" }).click();
  await expect(page.getByLabel("Muster F Mo", { exact: true })).toHaveValue("0");
  await page.getByRole("tab", { name: "Fachkraft" }).click();
  await expect(page.getByLabel("Muster F Mo", { exact: true })).toHaveValue("3");
  await page.getByRole("button", { name: "Zurücksetzen" }).click();
  await expect(cell("F", "05.01.2026")).toHaveValue("0");
  await expect(cell("F", "03.01.2026")).toHaveValue("2");
  await expect(changed).toHaveCount(0);
});

test("an invalid count is rejected by the API and kept for correction", async ({ page }) => {
  await page.goto("/staffing?month=2026-01&stations=101,102");
  const input = page.getByLabel("S am 07.01.2026", { exact: true });
  await input.fill("-1");
  await expect(input).toHaveAttribute("aria-invalid", "true");
  await page.getByRole("button", { name: "Speichern" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Mindestbesetzung ungültig" })).toBeVisible();
  await expect(input).toHaveValue("-1");
  await input.fill("");
  await expect(input).toHaveValue("0");
  await expect(input).toHaveAttribute("aria-invalid", "false");
});

test("a failed demand save keeps the unsaved edits", async ({ page }) => {
  await page.goto("/staffing?month=2026-01&stations=101,102");
  await page.getByRole("link", { name: "Example Station South" }).click();
  await expect(page).toHaveURL(/station=102/);
  const input = page.getByLabel("N am 10.01.2026", { exact: true });
  await input.fill("4");
  await page.getByRole("button", { name: "Speichern" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "nicht gespeichert" })).toBeVisible();
  await expect(page.getByRole("status")).toHaveCount(0);
  await expect(input).toHaveValue("4");
  await expect(input).toHaveAttribute("data-changed", "true");
  await expect(page.getByText("1 ungespeicherte Änderung")).toBeVisible();
});
