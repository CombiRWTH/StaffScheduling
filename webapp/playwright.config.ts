import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:18081", trace: "retain-on-failure" },
  webServer: [
    {
      command: "cd ../api && uv run --frozen python tests/browser_server.py",
      env: { PYTHONPATH: "." },
      url: "http://127.0.0.1:18080/status",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "pnpm dev --hostname 127.0.0.1 --port 18081",
      url: "http://127.0.0.1:18081",
      env: { SOLVER_API_URL: "http://127.0.0.1:18080" },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
