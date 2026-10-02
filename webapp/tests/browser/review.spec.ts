import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";

// The offline API (api/tests/browser_server.py) solves June for Station North for real. The schedule
// under review lives in that process only; each generation or valid import replaces it.

const JUNE = "/review?month=2026-06&stations=101";
const summary = (page: Page) => page.getByLabel("Dienstplan zur Prüfung");

async function generateJune(page: Page) {
  await page.goto("/generation?month=2026-06&stations=101");
  await page.getByLabel("Maximale Laufzeit (Sekunden)").fill("30");
  await page.getByRole("button", { name: "Starten" }).click();
  // The scope tells this job from a previous one of another station that is already finished.
  await expect(page.getByLabel("Letzte Generierung")).toContainText(
    "Juni 2026 (01.06.2026–30.06.2026) · Example Station North",
  );
  await expect(page.getByLabel("Letzte Generierung")).toContainText("Abgeschlossen", { timeout: 20_000 });
  await page.getByRole("link", { name: "Dienstplan prüfen" }).click();
}

async function download(page: Page, name: string) {
  const [file] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name }).click()]);
  expect(file.suggestedFilename()).toBe(name);
  return readFile((await file.path())!, "utf8");
}

async function upload(page: Page, input: string, result: string) {
  await page
    .getByLabel("input.json")
    .setInputFiles({ name: "input.json", mimeType: "application/json", buffer: Buffer.from(input) });
  await page
    .getByLabel("result.json")
    .setInputFiles({ name: "result.json", mimeType: "application/json", buffer: Buffer.from(result) });
  await page.getByRole("button", { name: "Importieren" }).click();
}

test("a generated schedule is reviewed with its check, staffing and accounts, and downloads its bundle", async ({
  page,
}) => {
  await generateJune(page);
  await expect(page).toHaveURL(JUNE);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Dienstplan prüfen");
  await expect(summary(page)).toContainText("Juni 2026 (01.06.2026–30.06.2026) · Example Station North · Generiert");
  await expect(summary(page)).toContainText("Regeln eingehalten");
  await expect(summary(page)).toContainText("Freie Sonntage im Jahr");
  await expect(summary(page)).toContainText("über den Monat hinaus");
  await expect(summary(page)).toContainText("Optimalitätslücke");
  // Solver settings and bounds are optional detail, collapsed until opened.
  await expect(summary(page).getByText("Gewichte")).toBeHidden();
  // Keyboard users open the collapsed section like any other control.
  await summary(page).getByText("Solver-Details").press("Enter");
  await expect(summary(page).getByText("Gewichte")).toBeVisible();

  const grid = page.getByLabel("Dienstplan", { exact: true });
  await expect(grid.getByRole("rowheader", { name: /Example Jumper Three/ })).toBeVisible();
  await expect(grid.getByText("Besetzung Example Station North")).toBeVisible();
  // June 5 and 6 each need one professional in the early shift; the solver may assign more.
  await expect(grid.getByText(/^[1-9]\/1$/)).toHaveCount(2);
  await grid.getByRole("button", { name: "Kompakt" }).click();
  await expect(grid.getByRole("button", { name: "Kompakt" })).toHaveAttribute("aria-pressed", "true");
  await grid.getByLabel("Mitarbeiter im Dienstplan suchen").fill("Three");
  await expect(grid.getByRole("rowheader", { name: /Example Team Two/ })).toBeHidden();

  // Every participant has an account row, also without duties.
  await expect(page.getByLabel("Monatskonten").getByRole("row")).toHaveCount(4);

  const schedule = await download(page, "schedule.csv");
  expect(schedule.split("\n")[0]).toBe(
    "employee_id,employee_name,date,weekday,is_public_holiday,planning_unit_id,planning_unit_name,shift_id," +
      "shift_code,shift_type,start_at,end_at,net_work_minutes,staff_level,origin_unit_id,origin_unit_name," +
      "origin_unit_type",
  );
  const employees = await download(page, "employees.csv");
  expect(employees.trim().split("\n")).toHaveLength(4);
  const result = JSON.parse(await download(page, "result.json"));
  expect(result.input.file).toBe("input.json");
  expect(result.solution.check.status).toBe("accepted");
  expect(JSON.parse(await download(page, "input.json")).dataset.planning_month).toEqual({ year: 2026, month: 6 });
});

test("a downloaded pair is imported; a rejected pair names its reason and keeps the current review", async ({
  page,
}) => {
  await page.goto(JUNE);
  await expect(summary(page)).toBeVisible();
  const input = await download(page, "input.json");
  const result = await download(page, "result.json");

  await upload(page, input, result);
  await expect(summary(page)).toContainText("Importiert");
  const imported = await summary(page).textContent();

  // Each reason the backend names is covered by the API tests; this one shows how a rejection reads.
  const otherInput = JSON.parse(input);
  otherInput.dataset.monthly_work_accounts[0].target_minutes += 1;
  await upload(page, JSON.stringify(otherInput), result);
  const alert = page.getByRole("alert").filter({ hasText: "Der bisherige Dienstplan bleibt zur Prüfung." });
  await expect(alert).toContainText("gehört zu einer anderen input.json");
  await expect(summary(page)).toHaveText(imported!);
});

test("a schedule of another scope is not shown as the selected one", async ({ page }) => {
  await page.goto("/review?month=2026-07&stations=101");
  await expect(page.getByText("Anderer Planungsumfang")).toBeVisible();
  await expect(page.getByText("gehört zu Juni 2026 · Example Station North")).toBeVisible();
  await expect(summary(page)).toBeHidden();
  await page.getByRole("link", { name: "Zu diesem Umfang wechseln" }).click();
  await expect(page).toHaveURL(JUNE);
  await expect(summary(page)).toBeVisible();
});
