import { request, type FullConfig } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

export default async function setup(config: FullConfig) {
  const origin = String(config.projects[0].use.baseURL);
  const context = await request.newContext({ baseURL: origin });
  try {
    const response = await context.post("/api/v1/session", {
      data: { token: "browser-fixture-launch-token-" + "a".repeat(32) },
      headers: { Origin: origin },
    });
    if (!response.ok())
      throw new Error("Fixture browser session could not be initialized.");
    const target = resolve("test-results/session.json");
    await mkdir(dirname(target), { recursive: true, mode: 0o700 });
    await writeFile(target, JSON.stringify(await context.storageState()), {
      mode: 0o600,
    });
  } finally {
    await context.dispose();
  }
}
