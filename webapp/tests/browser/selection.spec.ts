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
const defaultMonth = `${new Date().getFullYear()}-01`;

test("select both stations, inspect stable employees and jumper pool facts, then change scope", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(`/?month=${defaultMonth}`);
  await expect(page.getByRole("combobox", { name: "Monat" })).toHaveText("Januar");
  await expect(page.getByRole("button", { name: "Vorheriger Monat" })).toHaveCount(0);
  const year = page.getByRole("spinbutton", { name: "Jahr" });
  await year.fill("2026");
  await year.press("Enter");
  await expect(page).toHaveURL(/month=2026-01/);
  await toggleStation(page, "Example Station North");
  await expect(page.getByRole("checkbox", { name: "Example Station North" })).toBeChecked();
  await toggleStation(page, "Example Station South");
  await expect(page.getByRole("checkbox", { name: "Example Station South" })).toBeChecked();
  await closeStations(page);
  // The button shows a count, so its width stays predictable; the accessible name lists the stations.
  await expect(
    page.getByRole("button", { name: "Stationen: Example Station North, Example Station South" }),
  ).toHaveText("2 Stationen");

  await page
    .getByRole("link", { name: /^Mitarbeiter/ })
    .first()
    .click();
  await expect(page).toHaveURL(/stations=101%2C102/);
  await expect(page.getByText("Januar 2026 · Example Station North, Example Station South")).toBeVisible();
  await expect(page.getByText("Example Jumper Pool", { exact: true }).first()).toBeVisible();
  await expect(rows(page)).toHaveCount(4);

  await page.getByRole("button", { name: "Details für Example MFA One" }).click();
  const details = page.getByRole("row").filter({ hasText: "Zuordnungen" });
  await expect(details.getByText("160:00 h", { exact: true })).toBeVisible();
  await expect(details.getByText("8:00 h", { exact: true })).toBeVisible();
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

  await chooseMonth(page, "März");
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
  await expect(page.getByText("Bitte mindestens eine Station auswählen.", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
});

test("a subpage links back to the overview with the selection kept", async ({ page }) => {
  await page.goto("/employees?month=2026-01&stations=101");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mitarbeiter");
  await page.getByRole("link", { name: "Zurück zur Übersicht" }).click();
  await expect(page).toHaveURL("/?month=2026-01&stations=101");
  await expect(page.getByRole("link", { name: /^Zurück zu/ })).toHaveCount(0);
});

test("the overview welcomes the user; the sidebar links it and only the implemented areas", async ({ page }) => {
  await page.goto("/?month=2026-01&stations=101");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Übersicht");
  await expect(page.getByRole("region", { name: "Willkommen beim Schichtplan Manager" })).toContainText(
    "Wählen Sie oben Monat und Stationen",
  );
  const navigation = page.getByRole("navigation");
  await expect(navigation.getByRole("heading")).toHaveText(["Planungsdaten", "Dienstplan"]);
  await expect(navigation.getByRole("link", { name: "Übersicht" })).toHaveAttribute(
    "href",
    "/?month=2026-01&stations=101",
  );
  await expect(navigation.getByRole("link")).toHaveText([
    "Übersicht",
    "Mitarbeiter",
    "Verfügbarkeit",
    "Mindestbesetzung",
    "Erstellen",
    "Prüfen",
  ]);
});

test("the overview lists the planning pages in order and keeps the selection", async ({ page }) => {
  await page.goto("/?month=2026-01&stations=101");
  const steps = page.getByRole("list", { name: "Schritte" }).getByRole("link");
  await expect(steps).toHaveText([
    /^Mitarbeiter/,
    /^Verfügbarkeit/,
    /^Mindestbesetzung/,
    /^Dienstplan erstellen/,
    /^Dienstplan prüfen/,
  ]);
  await steps.first().click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mitarbeiter");
  await expect(page).toHaveURL(/\?month=2026-01&stations=101$/);
  // Pages are reached through the sidebar and the overview; there is no next-step link at the bottom.
  await expect(page.getByRole("link", { name: /^Weiter mit/ })).toHaveCount(0);
});

test("year entry keeps the month, a missing or invalid month defaults to January", async ({ page }) => {
  await page.goto("/employees?month=2026-01&stations=101");
  await expect(page.getByText("Example Team Two", { exact: true })).toBeVisible();
  const year = page.getByRole("spinbutton", { name: "Jahr" });
  await year.fill("2025");
  await year.press("Enter");
  await expect(page).toHaveURL(/month=2025-01/);
  await year.fill("1999");
  await year.press("Enter");
  await expect(year).toHaveValue("2025");

  for (const query of ["month=2026-13&stations=101", "stations=101"]) {
    await page.goto(`/employees?${query}`);
    await expect(page).toHaveURL(`/employees?month=${defaultMonth}&stations=101`);
  }
  await page.goto("/employees?month=2026-01&stations=abc");
  await expect(page.getByText("Bitte mindestens eine Station auswählen.", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
});

test("mobile navigation opens, keeps the selection and closes", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?month=2026-01&stations=101");
  await page.getByRole("button", { name: "Navigation öffnen" }).click();
  const link = page.getByRole("navigation").getByRole("link", { name: "Mitarbeiter" });
  await expect(link).toHaveAttribute("href", "/employees?month=2026-01&stations=101");
  await expect(page.getByRole("navigation").getByRole("link").filter({ visible: true })).toHaveCount(6);
  await link.click();
  await expect(page).toHaveURL(/\/employees\?month=2026-01&stations=101/);
  await expect(page.getByRole("button", { name: "Navigation öffnen" })).toBeVisible();
  await expect(page.getByRole("navigation")).toHaveCount(0);
});
