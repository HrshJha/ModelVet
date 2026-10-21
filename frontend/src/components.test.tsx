import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { formatBytes, shortDigest } from "./api";
import { Badge, CheckGlyph, DecisionMark, Notice } from "./components";
import { checkStatus } from "./ReportView";

describe("local review presentation contracts", () => {
  it.each(["APPROVE", "CONTROLS", "BLOCK", "INSUFFICIENT"])(
    "labels %s without relying on color",
    (state) => {
      expect(renderToStaticMarkup(<Badge state={state} />)).toContain(state);
    },
  );
  it("escapes hostile artifact text", () => {
    const html = renderToStaticMarkup(
      <Notice>{"<img src=x onerror=alert(1)>"}</Notice>,
    );
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;img");
  });
  it.each([
    "COMPLETE",
    "SKIPPED",
    "FAILED",
    "UNSUPPORTED",
    "INCONCLUSIVE",
    "NOT_RUN",
  ])("distinguishes the %s execution state with a word and glyph", (state) => {
    const html = renderToStaticMarkup(<CheckGlyph status={state} required />);
    expect(html).toContain(state);
    expect(html).toContain("Mandatory check");
    expect(html).toContain("check-" + state.toLowerCase());
  });
  it("gives each admission outcome a distinct shape and scoped explanation", () => {
    const states = ["APPROVE", "CONTROLS", "BLOCK", "INSUFFICIENT"];
    const html = states.map((state) =>
      renderToStaticMarkup(<DecisionMark state={state} />),
    );
    states.forEach((state, index) =>
      expect(html[index]).toContain("decision-" + state.toLowerCase()),
    );
    expect(
      new Set(html.map((value) => value.match(/decision-shape[^>]*>/)?.[0]))
        .size,
    ).toBe(1);
    expect(html.join(" ")).toContain("malware freedom");
    expect(html.join(" ")).toContain("neither an approval nor a finding");
  });
  it("uses binary byte units and shortened identities", () => {
    expect(formatBytes(1024)).toBe("1.0 KiB");
    expect(shortDigest("sha256:" + "a".repeat(64))).toBe("a".repeat(12));
  });
  it("never fills absent or contradictory check observations with completion", () => {
    const expected = { expected_check_ids: ["identity"] };
    expect(checkStatus(expected, "identity")).toBe("INCONCLUSIVE");
    expect(
      checkStatus(
        { ...expected, completed_check_ids: ["identity"] },
        "identity",
      ),
    ).toBe("COMPLETE");
    expect(
      checkStatus(
        {
          ...expected,
          completed_check_ids: ["identity"],
          failed_check_ids: ["identity"],
        },
        "identity",
      ),
    ).toBe("INCONCLUSIVE");
  });
});
