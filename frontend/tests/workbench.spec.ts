import {
  test,
  expect,
  type BrowserContextOptions,
  type Page,
} from "@playwright/test";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";

const externalRequests = new WeakMap<Page, string[]>();
test.beforeEach(async ({ page }) => {
  const requests: string[] = [];
  externalRequests.set(page, requests);
  page.on("request", (request) => {
    if (new URL(request.url()).origin !== "http://127.0.0.1:48231")
      requests.push(request.url());
  });
});
test.afterEach(async ({ page }) => {
  expect(externalRequests.get(page)).toEqual([]);
});

let authenticated: NonNullable<BrowserContextOptions["storageState"]>;
test.beforeAll(async () => {
  authenticated = JSON.parse(
    await readFile(
      new URL("../test-results/session.json", import.meta.url),
      "utf8",
    ),
  );
});

test("overview has real empty state and working navigation", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Evidence before execution." }),
  ).toBeVisible();
  await expect(
    page.getByText("Your first evidence trail starts here."),
  ).toBeVisible();
  await expect(page.locator(".root-label")).toContainText("models");
  await page.screenshot({
    path: info.outputPath("overview-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Jump to…" }).click();
  await page.getByRole("textbox", { name: "Find a page" }).fill("environment");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Environment" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Know your environment." }),
  ).toBeVisible();
});

test("folder browser runs a genuine supported static scan", async ({
  page,
}, info) => {
  await page.goto("/#/scan");
  await page.getByRole("button", { name: "Browse folders" }).click();
  await page
    .getByRole("button", { name: "tiny-safetensors", exact: true })
    .click();
  await page.getByRole("button", { name: "Use this folder" }).click();
  await expect(page.getByLabel("Model folder")).toHaveValue("tiny-safetensors");
  await page.screenshot({
    path: info.outputPath("scan-setup-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.getByRole("heading", { name: "tiny-safetensors" }),
  ).toBeVisible({ timeout: 15000 });
  await expect(
    page.locator(".verdict-panel").getByText("APPROVE", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /weights.safetensors/ }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("report-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: /weights.safetensors/ }).click();
  await page.getByRole("button", { name: "Inspect record" }).first().click();
  await expect(
    page.getByRole("dialog", { name: "Evidence detail" }),
  ).toBeVisible();
  await expect(page.getByRole("dialog").locator("pre")).toContainText(
    "file_id",
  );
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "Findings", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No findings recorded." }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Files & coverage" }).click();
  await page.getByRole("link", { name: "Scan history", exact: true }).click();
  await expect(
    page.getByRole("link", { name: /tiny-safetensors/ }),
  ).toBeVisible();
});

async function selectFolder(page: Page, name: string) {
  await page.getByRole("button", { name: "Browse folders" }).click();
  await page.getByRole("button", { name, exact: true }).click();
  await page.getByRole("button", { name: "Use this folder" }).click();
}

test("BLOCK, INSUFFICIENT and CONTROLS remain distinct completed outcomes", async ({
  page,
}) => {
  for (const [folder, decision] of [
    ["with-repository-code", "BLOCK"],
    ["unknown-content", "INSUFFICIENT"],
  ]) {
    await page.goto("/#/scan");
    await selectFolder(page, folder);
    await page.getByRole("button", { name: "Start scan" }).click();
    await expect(page.getByRole("heading", { name: folder })).toBeVisible();
    await expect(
      page.locator(".verdict-panel").getByText(decision, { exact: true }),
    ).toBeVisible();
  }
  await page.goto("/#/scan");
  await selectFolder(page, "tiny-safetensors");
  await page
    .getByLabel("Choose policy TOML")
    .setInputFiles({
      name: "controls.toml",
      mimeType: "text/plain",
      buffer: await readFile(
        new URL("../../examples/controls.toml", import.meta.url),
      ),
    });
  await expect(
    page.getByText("Imported and validated TOML policy"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.locator(".verdict-panel").getByText("CONTROLS", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".control-owner")).toContainText("Owner:");
});

test("original JSON download/import and attachment checks preserve stored admission", async ({
  page,
}, info) => {
  await page.goto("/#/history");
  await page
    .getByRole("link", { name: /tiny-safetensors/ })
    .first()
    .click();
  await expect(page.locator(".verdict-panel")).toBeVisible();
  const key = page.url().split("/reports/")[1];
  const original = await (
    await page.request.get(`/api/v1/reports/${key}/download`)
  ).body();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("link", { name: "JSON", exact: true }).click(),
  ]);
  const target = info.outputPath("downloaded-report.json");
  await download.saveAs(target);
  expect(await readFile(target)).toEqual(original);
  await page.getByRole("link", { name: "Scan history", exact: true }).click();
  await page
    .getByLabel("Choose report JSON")
    .setInputFiles({
      name: "review.json",
      mimeType: "application/json",
      buffer: original,
    });
  await expect(
    page.getByRole("heading", { name: "Imported report", exact: true }),
  ).toBeVisible();
  const imported = page.url().split("/reports/")[1];
  expect(
    await (
      await page.request.get(`/api/v1/reports/${imported}/download`)
    ).body(),
  ).toEqual(original);
  await page
    .getByRole("button", { name: "Verify attachments", exact: true })
    .click();
  await expect(
    page.getByText(/No scanner raw attachments were declared/),
  ).toBeVisible();
  await expect(
    page.locator(".verdict-panel").getByText("CONTROLS", { exact: true }),
  ).toBeVisible();
});

test("comparison exposes exact changes without recomputing decisions", async ({
  page,
}, info) => {
  await page.goto("/#/compare");
  await page
    .getByRole("button", { name: /BEFORE Select a baseline report/ })
    .click();
  await page
    .getByRole("dialog")
    .locator(".picker-list > button")
    .filter({ hasText: "tiny-safetensors" })
    .filter({ has: page.locator(".badge.approve") })
    .click();
  await page
    .getByRole("button", { name: /AFTER Select a report to compare/ })
    .click();
  await page
    .getByRole("dialog")
    .locator(".picker-list > button")
    .filter({ hasText: "unknown-content" })
    .click();
  await page
    .getByRole("button", { name: "Compare reports", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Semantic changes recorded." }),
  ).toBeVisible();
  await expect(
    page.locator(".comparison-result .badge.insufficient"),
  ).toBeVisible();
  await expect(
    page
      .locator(".changes-panel")
      .first()
      .getByText("opaque.bin", { exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Show relative filenames in results").check();
  await page
    .getByRole("button", { name: "Compare reports", exact: true })
    .click();
  await expect(
    page
      .locator(".changes-panel")
      .first()
      .getByText("opaque.bin", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("comparison-desktop.png"),
    fullPage: true,
  });
  await expect(page.getByText(/No admission recomputed/)).toBeVisible();
});

test("cancellation stops a real worker and never produces an admission result", async ({
  page,
}) => {
  await page.goto("/#/scan");
  await selectFolder(page, "serialized-fixture");
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.getByRole("heading", { name: "Collect scanner evidence" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel scan", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Assessment stopped." }),
  ).toBeVisible();
  await expect(page.getByText(/No completed report was indexed/)).toBeVisible();
  await expect(page.locator(".verdict-panel")).toHaveCount(0);
});

for (const width of [375, 768, 1024, 1440]) {
  test(`responsive and accessible review at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/#/");
    await expect(
      page.getByRole("heading", { name: "Evidence before execution." }),
    ).toBeVisible();
    await expect(page.locator(".root-label")).toContainText("models");
    await expect(page.locator(".recent-panel tbody tr")).toHaveCount(5);
    expect(await page.evaluate(() => innerWidth)).toBe(width);
    const overflow = await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
      nodes: Array.from(document.querySelectorAll("body *"))
        .filter(
          (node) =>
            node.getBoundingClientRect().right > innerWidth + 0.5 &&
            !node.closest(".table-wrap,.tabs,.sr-only"),
        )
        .map((node) => ({
          name: node.getAttribute("class") || node.tagName,
          right: node.getBoundingClientRect().right,
        })),
    }));
    if (overflow.scroll > overflow.width) {
      const textOverflow = await page.evaluate(() => {
        const walker = document.createTreeWalker(
          document.body,
          NodeFilter.SHOW_TEXT,
        );
        const rows = [];
        let node;
        while ((node = walker.nextNode())) {
          if (
            !node.textContent?.trim() ||
            node.parentElement?.closest(".table-wrap,.tabs,.sr-only")
          )
            continue;
          const range = document.createRange();
          range.selectNodeContents(node);
          const rect = range.getBoundingClientRect();
          if (rect.right > innerWidth + 0.5)
            rows.push({
              parent:
                node.parentElement?.getAttribute("class") ||
                node.parentElement?.tagName,
              right: rect.right,
              length: node.textContent.length,
            });
        }
        return rows;
      });
      console.log(JSON.stringify({ ...overflow, textOverflow }));
    }
    expect(overflow.scroll <= overflow.width).toBeTruthy();
    const overview = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(overview.violations).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`overview-${width}.png`),
      fullPage: true,
    });
    await page.getByRole("link", { name: "Scan history", exact: true }).click();
    await page
      .getByRole("link", { name: /unknown-content/ })
      .first()
      .click();
    await expect(
      page.locator(".verdict-panel").getByText("INSUFFICIENT", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /opaque.bin/ }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    const report = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(report.violations).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`report-${width}.png`),
      fullPage: true,
    });
  });
}

test("hostile declaration text never becomes browser markup", async ({
  page,
}) => {
  await page.goto("/#/scan");
  await selectFolder(page, "hostile-metadata");
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.getByRole("heading", { name: "hostile-metadata" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Declarations", exact: true }).click();
  await expect(
    page
      .getByRole("tabpanel")
      .getByText("<img src=x onerror=window.__modelvet_xss=1>", {
        exact: true,
      }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => (window as unknown as Record<string, unknown>).__modelvet_xss,
    ),
  ).toBeUndefined();
  await expect(page.locator("img")).toHaveCount(0);
});

test("disconnected progress keeps the last observed state and can reconnect", async ({
  page,
}) => {
  await page.goto("/#/scan");
  await selectFolder(page, "serialized-fixture");
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(
    page.getByRole("heading", { name: "Collect scanner evidence" }),
  ).toBeVisible();
  try {
    await page.route("**/api/v1/scans/*", (route) =>
      route.abort("connectionrefused"),
    );
    await expect(
      page.getByText(
        /Reconnecting does not change the last recorded job state/,
      ),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Following the evidence." }),
    ).toBeVisible();
    await expect(page.locator(".verdict-panel")).toHaveCount(0);
  } finally {
    await page.unroute("**/api/v1/scans/*");
    await page
      .getByRole("button", { name: "Cancel scan", exact: true })
      .click();
  }
  await expect(
    page.getByRole("heading", { name: "Assessment stopped." }),
  ).toBeVisible();
});

test("keyboard and coarse-pointer controls remain usable", async ({
  browser,
}) => {
  const context = await browser.newContext({
    storageState: authenticated,
    viewport: { width: 375, height: 900 },
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  try {
    await page.goto("http://127.0.0.1:48231/#/scan");
    await expect(
      page.getByRole("heading", { name: "Start with the evidence." }),
    ).toBeVisible();
    for (const locator of [
      page.getByRole("button", { name: "Browse folders" }),
      page.getByRole("button", { name: "Start scan" }),
      page.getByRole("button", { name: "Jump to…" }),
    ]) {
      const box = await locator.boundingBox();
      expect(box!.width).toBeGreaterThanOrEqual(44);
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }
    await page.keyboard.press("Control+k");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => matchMedia("(prefers-reduced-motion: reduce)").matches,
      ),
    ).toBeTruthy();
  } finally {
    await context.close();
  }
});
