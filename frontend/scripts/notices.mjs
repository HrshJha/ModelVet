import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const notices = [];
for (const name of [
  "react",
  "react-dom",
  "scheduler",
  "lucide-react",
  "vite",
]) {
  const root = resolve("node_modules", name);
  const metadata = JSON.parse(
    await readFile(resolve(root, "package.json"), "utf8"),
  );
  let license;
  for (const filename of ["LICENSE", "LICENSE.md", "LICENSE.txt"]) {
    try {
      license = await readFile(resolve(root, filename), "utf8");
      break;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }
  if (!license) throw new Error(`No license notice found for ${name}.`);
  notices.push(`${name} ${metadata.version}\n${"=".repeat(60)}\n${license}`);
}
await writeFile(
  "../src/modelvet/workbench/static/THIRD_PARTY_NOTICES.txt",
  notices.join("\n\n"),
);
