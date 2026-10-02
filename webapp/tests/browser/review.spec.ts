import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";

// The offline API (api/tests/browser_server.py) solves June for Station North for real. The schedule
// under review lives in that process only; each generation or valid import replaces it.

const JUNE = "/review?month=2026-06&stations=101";
const summary = (page: Page) => page.getByLabel("Dienstplan zur Prüfung");

async function generateJune(page: Page) {
  await page.goto("/generation?month=2026-06&stations=101");
  await page.getByLabel("Maximale Laufzeit").fill("30");
  await page.getByRole("button", { name: "Starten" }).click();
  // The scope tells this job from a previous one of another station that is already finished.
  await expect(page.getByLabel("Letzte Generierung")).toContainText(
    "Juni 2026 (01.06.2026–30.06.2026) · Example Station North",
  );
  await expect(page.getByLabel("Letzte Generierung")).toContainText("Abgeschlossen", { timeout: 20_000 });
  await page.getByRole("link", { name: "Dienstplan prüfen" }).click();
}

/** Download one file of the schedule under review through the Herunterladen menu. */
async function download(page: Page, name: string) {
  await page.getByRole("button", { name: "Herunterladen" }).click();
  const menu = page.getByRole("dialog", { name: "Herunterladen" });
  const [file] = await Promise.all([page.waitForEvent("download"), menu.getByRole("link", { name }).click()]);
  await page.keyboard.press("Escape");
  expect(file.suggestedFilename()).toBe(name);
  return readFile((await file.path())!, "utf8");
}

/** Import a pair through the Importieren popover; it closes only when the import succeeded. */
async function upload(page: Page, input: string, result: string) {
  const form = page.getByRole("dialog", { name: "Importieren" });
  if (!(await form.isVisible())) await page.getByRole("button", { name: "Importieren" }).click();
  await form
    .getByLabel("input.json")
    .setInputFiles({ name: "input.json", mimeType: "application/json", buffer: Buffer.from(input) });
  await form
    .getByLabel("result.json")
    .setInputFiles({ name: "result.json", mimeType: "application/json", buffer: Buffer.from(result) });
  await form.getByRole("button", { name: "Dateien importieren" }).click();
}

test("a generated schedule is reviewed with its check, staffing and accounts, and downloads its bundle", async ({
  page,
}) => {
  await generateJune(page);
  await expect(page).toHaveURL(JUNE);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Dienstplan prüfen");
  await expect(summary(page).getByRole("heading")).toHaveText("Juni 2026 · Example Station North");
  await expect(summary(page)).toContainText("Generiert");
  await expect(summary(page)).toContainText("Regeln eingehalten");
  await expect(summary(page)).toContainText("Kann veröffentlicht werden; Lücken werden nicht veröffentlicht");
  // Required slots nobody can fill are listed prominently, apart from the duties.
  const gaps = summary(page).getByRole("region", { name: "Lücken" });
  await expect(gaps).toContainText("1 unbesetzte Pflichtstelle (Lücken)");
  await expect(gaps).toContainText("05.06.2026 · Example Station North · F · Fachkraft: 1 von 2 fehlen");
  // Wishes never bind: the review counts and lists what the schedule made of each.
  const wishes = summary(page).getByRole("region", { name: "Wünsche" });
  const wishTitle = wishes.getByText("Wünsche: 1 erfüllt · 1 nicht erfüllt · 1 nicht erfüllbar");
  // The table stays collapsed until opened.
  await expect(wishes.getByRole("table")).toBeHidden();
  await wishTitle.click();
  await expect(wishes.getByRole("row", { name: "05.06.2026 Example Team Two Freier Tag nicht erfüllt" })).toBeVisible();
  await expect(
    wishes.getByRole("row", { name: "11.06.2026 Example Jumper Three Wunschtag nicht erfüllbar" }),
  ).toBeVisible();
  // Solver internals and obligations beyond the month are technical detail, collapsed until opened.
  const details = summary(page).getByText("Technische Details");
  await expect(summary(page).getByText("Stufe 1: Lücken")).toBeHidden();
  // Keyboard users open the collapsed section like any other control.
  await details.press("Enter");
  await expect(summary(page).getByText("Stufe 1: Lücken")).toBeVisible();
  await expect(summary(page).getByText("Stufe 3: Wunschkosten (Fairness)")).toBeVisible();
  await expect(summary(page).getByText("Stufe 5: Überzählige Zwischendienste")).toBeVisible();
  await expect(summary(page)).toContainText("Freie Sonntage im Jahr");

  const grid = page.getByLabel("Dienstplan", { exact: true });
  await expect(grid.getByRole("rowheader", { name: /Example Jumper Three/ })).toBeVisible();
  await expect(grid.getByText("Besetzung Example Station North")).toBeVisible();
  // June 6 needs one professional in the early shift, the solver may assign more; June 5 stays short by its gap,
  // also when the MFA works that early, which another qualification cannot fill.
  await expect(grid.getByText(/^[1-9]\/1$/)).toHaveCount(1);
  await expect(grid.locator('td[title*="Fachkraft 1/2"]')).toHaveClass(/text-destructive/);
  // The jumper-pool MFA's duties at the station are transfers; the station employee works at home.
  const mfa = grid.getByRole("row", { name: /Example MFA One/ });
  const team = grid.getByRole("row", { name: /Example Team Two/ });
  // Each duty names its origin to screen readers; a transfer also says that it lies outside it.
  await expect(mfa.getByText(/Herkunft Example Jumper Pool, Einsatz außerhalb der Herkunft/).first()).toBeAttached();
  await expect(team.getByText(/Herkunft Example Station North/).first()).toBeAttached();
  await expect(team.getByText(/Einsatz außerhalb der Herkunft/)).toHaveCount(0);
  // The employee column names the origin; with one station selected, no duty repeats a unit name.
  await expect(mfa.getByRole("rowheader")).toContainText("Example Jumper Pool");
  await expect(mfa.getByRole("cell").getByText("Example Station North", { exact: true })).toHaveCount(0);
  await expect(grid.getByRole("button", { name: "Kompakt" })).toHaveCount(0);
  await expect(grid.getByLabel("Legende")).toContainText("Einsatz außerhalb der Herkunft");
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
  const gapRows = (await download(page, "gaps.csv")).trim().split("\n");
  expect(gapRows).toEqual([
    "planning_unit_id,planning_unit_name,date,shift_id,shift_code,staff_level,required_count,assigned_count,missing_count",
    "101,Example Station North,2026-06-05,1113,F,professional,2,1,1",
  ]);
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
  // A successful import closes its popover and replaces the review.
  await expect(page.getByRole("dialog", { name: "Importieren" })).toBeHidden();
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

test("a home change within the month marks only the duties after it as transfers", async ({ page }) => {
  await page.goto(JUNE);
  const input = JSON.parse(await download(page, "input.json"));
  const result = JSON.parse(await download(page, "result.json"));
  // Team Two's home moves from Station North to the jumper pool on June 16; a replacement membership keeps
  // the station duties eligible, so the schedule and its check stay the same.
  const memberships = input.dataset.planning_unit_memberships;
  const home = memberships.find((row: { employee_id: number }) => row.employee_id === 2);
  memberships.push(
    { ...home, valid_from: "2026-06-16", planning_unit_id: 201 },
    { ...home, valid_from: "2026-06-16", is_home: false, is_replacement: true },
  );
  home.valid_until = "2026-06-15";
  const changed = JSON.stringify(input);
  result.input.sha256 = createHash("sha256").update(changed).digest("hex");
  await upload(page, changed, JSON.stringify(result));
  await expect(summary(page)).toContainText("Importiert");

  const team = page.getByLabel("Dienstplan", { exact: true }).getByRole("row", { name: /Example Team Two/ });
  await expect(team.getByRole("rowheader")).toContainText("Example Station North, Example Jumper Pool");
  // One cell per day; a duty's text names its origin, a transfer's also that it lies outside it.
  const days = (await team.getByRole("cell").allTextContents()).map((text, index) => ({ day: index + 1, text }));
  const duties = days.filter(({ text }) => text.includes("Herkunft"));
  const transfer = ({ text }: { text: string }) => text.includes("Einsatz außerhalb der Herkunft");
  expect(duties.filter(({ day }) => day <= 15).some(transfer)).toBe(false);
  expect(duties.filter(({ day }) => day >= 16).every(transfer)).toBe(true);
  expect(duties.some(({ day }) => day <= 15) && duties.some(({ day }) => day >= 16)).toBe(true);
});

test("a duty without a dated membership has an unknown origin and an eligibility finding", async ({ page }) => {
  await page.goto(JUNE);
  const input = JSON.parse(await download(page, "input.json"));
  const result = JSON.parse(await download(page, "result.json"));
  // Every membership of Team Two, also those of the earlier home change, ends the day before their last duty,
  // which then has no origin. Such a schedule is rejected; its result carries the finding the re-check names.
  type Duty = { employee_id: number; date: string; planning_unit_id: number; shift_id: number };
  const last = (result.solution.assignments as Duty[])
    .filter((row) => row.employee_id === 2)
    .reduce((latest, row) => (row.date > latest.date ? row : latest));
  const before = new Date(`${last.date}T00:00:00Z`);
  before.setUTCDate(before.getUTCDate() - 1);
  const cutoff = before.toISOString().slice(0, 10);
  type Membership = { employee_id: number; valid_from: string; valid_until: string };
  input.dataset.planning_unit_memberships = (input.dataset.planning_unit_memberships as Membership[])
    .filter((row) => row.employee_id !== 2 || row.valid_from <= cutoff)
    .map((row) => (row.employee_id === 2 && row.valid_until > cutoff ? { ...row, valid_until: cutoff } : row));
  const changed = JSON.stringify(input);
  result.input.sha256 = createHash("sha256").update(changed).digest("hex");
  result.solution.check.status = "rejected";
  result.solution.check.findings = [
    {
      rule: "eligibility",
      message: "No active professional membership at the station.",
      employee_id: 2,
      date: last.date,
      planning_unit_id: last.planning_unit_id,
      shift_id: last.shift_id,
    },
  ];
  await upload(page, changed, JSON.stringify(result));
  await expect(summary(page)).toContainText("Regelverstöße");

  const grid = page.getByLabel("Dienstplan", { exact: true });
  const team = grid.getByRole("row", { name: /Example Team Two/ });
  await expect(team.getByText(/Herkunft unbekannt/)).toHaveCount(1);
  await expect(grid.getByLabel("Legende")).toContainText("Herkunft unbekannt");
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
