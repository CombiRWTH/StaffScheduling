import { expect, test, type Page } from "@playwright/test";

async function chooseMonth(page: Page, month: string) {
  await page.getByRole("combobox", { name: "Monat" }).click();
  await page.getByRole("option", { name: month, exact: true }).click();
}

async function toggleStation(page: Page, name: string) {
  const station = page.getByRole("checkbox", { name });
  if (!(await station.isVisible())) await page.getByRole("button", { name: /^Stationen:/ }).click();
  await station.click();
}

async function closeStations(page: Page) {
  await page.keyboard.press("Escape");
}

const rows = (page: Page) => page.getByRole("row");

test("select both stations, inspect stable employees and pool facts, then change scope", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("spinbutton", { name: "Jahr" }).fill("2026");
  await chooseMonth(page, "Januar");
  await expect(page).toHaveURL(/month=2026-01/);
  await toggleStation(page, "Example Station North");
  await expect(page.getByRole("checkbox", { name: "Example Station North" })).toBeChecked();
  await toggleStation(page, "Example Station South");
  await expect(page.getByRole("checkbox", { name: "Example Station South" })).toBeChecked();
  await closeStations(page);
  await expect(page.getByRole("button", { name: "Stationen: 2 Stationen" })).toBeVisible();

  await page
    .getByRole("link", { name: /^Mitarbeiter/ })
    .first()
    .click();
  await expect(page).toHaveURL(/stations=101%2C102/);
  await expect(page.getByText("Januar 2026 · Example Station North, Example Station South")).toBeVisible();
  await expect(page.getByText("Example Shared Pool", { exact: true }).first()).toBeVisible();
  await expect(rows(page)).toHaveCount(4);

  await page.getByRole("button", { name: "Details für Example MFA One" }).click();
  const details = page.getByRole("row").filter({ hasText: "Datierte Mitgliedschaften" });
  await expect(details.getByText("9600 min", { exact: true })).toBeVisible();
  await expect(details.getByText("480 min", { exact: true })).toBeVisible();
  await expect(details.getByText(/01\.12\.2025 – 30\.06\.2026 · MFA · Heimat/)).toBeVisible();
  await expect(details.getByText(/· MFA · Ersatz/)).toHaveCount(2);
  await expect(details.getByText(/01\.01\.2026 · Urlaub · U/)).toBeVisible();
  await page.getByRole("button", { name: "Details für Example MFA One" }).click();

  await page.getByLabel("Mitarbeiter suchen").fill("1");
  await expect(rows(page)).toHaveCount(2);
  await page.getByLabel("Mitarbeiter suchen").fill("");
  await page.getByRole("combobox", { name: "Einheit filtern" }).click();
  await page.getByRole("option", { name: "Example Station North" }).click();
  await expect(rows(page)).toHaveCount(3);

  await chooseMonth(page, "Juni");
  await expect(page.getByText("Mitarbeiter für die neue Auswahl werden geladen…", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
  await expect(page.getByText("Juni 2026 · Example Station North, Example Station South")).toBeVisible();

  await chooseMonth(page, "Februar");
  await expect(page).toHaveURL(/month=2026-02&stations=102$/);
  await expect(page.getByText("Februar 2026 · Example Station South", { exact: true })).toBeVisible();
  await expect(page.getByText("Example Team Two", { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Nächster Monat" }).click();
  await expect(page).toHaveURL(/month=2026-03/);
  await expect(page.getByText("Keine Mitarbeiter für diese Auswahl vorhanden.", { exact: true })).toBeVisible();
  await expect(page.getByText("Example MFA One", { exact: true })).toHaveCount(0);
});

test("unavailable and incomplete reads are useful errors with no partial employee table", async ({ page }) => {
  await page.goto("/employees?month=2026-01&stations=101,102");
  await expect(page.getByText("Example MFA One", { exact: true })).toBeVisible();
  await chooseMonth(page, "April");
  await expect(page.getByText("Mitarbeiter nicht geladen")).toBeVisible();
  await expect(page.getByText("Example MFA One", { exact: true })).toHaveCount(0);
  await chooseMonth(page, "Mai");
  await expect(page.getByText(/Daten unvollständig\. Stationen/)).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
  await chooseMonth(page, "Januar");
  await page.getByRole("button", { name: "Stationen aktualisieren" }).click();
  await expect(page.getByText("Example MFA One", { exact: true })).toBeVisible();
  await toggleStation(page, "Example Station North");
  await expect(page.getByRole("checkbox", { name: "Example Station North" })).not.toBeChecked();
  await toggleStation(page, "Example Station South");
  await expect(page.getByRole("checkbox", { name: "Example Station South" })).not.toBeChecked();
  await expect(
    page.getByText("Bitte einen Planungsmonat und mindestens eine Station auswählen.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
});

test("unsupported areas are visible but not navigable", async ({ page }) => {
  await page.goto("/");
  const unsupported = page.locator('nav [aria-disabled="true"]');
  await expect(unsupported).toHaveCount(7);
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(1);
  await expect(page.getByText("Noch nicht unterstützt", { exact: true })).toHaveCount(2);
});
