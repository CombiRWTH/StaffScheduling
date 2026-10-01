import { expect, test } from "@playwright/test";

test("select both stations, inspect stable employees and pool facts, then change scope", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Planungsmonat").fill("2026-01");
  await page.getByLabel("Example Station North").click();
  await expect(page.getByLabel("Example Station North")).toBeChecked();
  await page.getByLabel("Example Station South").click();
  await expect(page.getByLabel("Example Station South")).toBeChecked();
  await page.getByRole("link", { name: "Mitarbeiter", exact: true }).click();
  await expect(page).toHaveURL(/stations=101%2C102/);
  await expect(page.getByText("Pool-Kontext: Example Shared Pool", { exact: true })).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(4);
  await page.getByText("Details für Example MFA One", { exact: true }).click();
  await expect(page.getByText("Ziel: 9600 · Ist: 0 · Verifizierte Gutschriften: 480", { exact: true })).toBeVisible();
  await expect(page.getByText(/Example Shared Pool \(shared_pool\).*mfa.*Heimat: ja/)).toBeVisible();
  await expect(page.getByText(/Example Station South \(station\).*mfa.*Ersatz: ja/)).toBeVisible();
  await expect(page.getByText(/2026-01-01 · vacation · U/)).toBeVisible();
  await page.getByLabel("Mitarbeiter suchen").fill("1");
  await expect(page.getByRole("row")).toHaveCount(2);
  await page.getByLabel("Mitarbeiter suchen").fill("");
  await page.getByLabel("Einheit filtern").selectOption("201");
  await expect(page.getByRole("row")).toHaveCount(3);
  await page.getByLabel("Planungsmonat").fill("2026-06");
  await expect(page.getByText("Mitarbeiter für die neue Auswahl werden geladen…", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
  await expect(
    page.getByText("2026-06-01 bis 2026-06-30 · Example Station North, Example Station South", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Planungsmonat").fill("2026-02");
  await expect(page.getByLabel("Example Station South")).toBeChecked();
  await expect(page.getByLabel("Example Station North")).toHaveCount(0);
  await expect(page).toHaveURL(/month=2026-02&stations=102$/);
  await expect(page.getByText("2026-02-01 bis 2026-02-28 · Example Station South", { exact: true })).toBeVisible();
  await expect(page.getByText("Example Team Two", { exact: true })).toHaveCount(0);
  await page.getByLabel("Planungsmonat").fill("2026-03");
  await expect(page.getByText("Keine Mitarbeiter für diese Auswahl vorhanden.", { exact: true })).toBeVisible();
  await expect(page.getByText("Example MFA One", { exact: true })).toHaveCount(0);
});

test("unavailable and incomplete reads are useful errors with no partial employee table", async ({ page }) => {
  await page.goto("/employees?month=2026-01&stations=101,102");
  await expect(page.getByText("Example MFA One", { exact: true })).toBeVisible();
  await page.getByLabel("Planungsmonat").fill("2026-04");
  await expect(page.getByRole("heading", { name: "Mitarbeiter nicht geladen" })).toBeVisible();
  await expect(page.getByText("Example MFA One", { exact: true })).toHaveCount(0);
  await page.getByLabel("Planungsmonat").fill("2026-05");
  await expect(page.getByText(/Daten unvollständig\. Stationen/)).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
  await page.getByLabel("Planungsmonat").fill("2026-01");
  await page.getByRole("button", { name: "Stationen aktualisieren" }).click();
  await expect(page.getByText("Example MFA One", { exact: true })).toBeVisible();
  await page.getByLabel("Example Station North").click();
  await expect(page.getByLabel("Example Station North")).not.toBeChecked();
  await page.getByLabel("Example Station South").click();
  await expect(page.getByLabel("Example Station South")).not.toBeChecked();
  await expect(
    page.getByText("Bitte einen Planungsmonat und mindestens eine Station auswählen.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
});
