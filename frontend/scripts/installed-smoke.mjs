import assert from "node:assert/strict";
import { chromium, expect } from "@playwright/test";

const origin = process.env.MODELVET_ACCEPTANCE_ORIGIN;
const cookie = process.env.MODELVET_ACCEPTANCE_COOKIE;
assert(origin && cookie, "Private acceptance session required");
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  await context.addCookies([
    {
      name: "modelvet_session",
      value: cookie,
      url: origin,
      httpOnly: true,
      sameSite: "Strict",
    },
  ]);
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const external = [];
  await context.route("**/*", async (route) => {
    if (new URL(route.request().url()).origin !== origin) {
      external.push(route.request().resourceType());
      await route.abort();
    } else await route.continue();
  });
  await page.goto(origin);
  await page
    .getByRole("heading", { name: "Evidence before execution." })
    .waitFor();
  await page.getByRole("link", { name: "New scan N", exact: true }).click();
  await page.getByRole("button", { name: "Browse folders" }).click();
  await page.getByRole("button", { name: "tiny", exact: true }).click();
  await page.getByRole("button", { name: "Use this folder" }).click();
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.getByRole("heading", { name: "tiny", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await expect(
    page.locator(".verdict-panel").getByText("APPROVE", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Scan history", exact: true }).click();
  await page
    .getByRole("heading", {
      name: "An evidence trail worth keeping.",
      exact: true,
    })
    .waitFor();
  await expect(
    page
      .getByRole("table")
      .getByRole("link", { name: /^tiny / })
      .first(),
  ).toBeVisible();
  assert.deepEqual(external, []);
  console.log(
    "Installed wheel browser: real scan and history, bundled assets, zero external requests.",
  );
} finally {
  await browser.close();
}
