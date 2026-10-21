# Workbench redesign verification

These captures come from the synthetic, inert Workbench fixtures. They are visual review evidence, not model-safety results.

- `overview-paper-1440.png` — overview in Paper theme at 1440px.
- `overview-night-1440.png` — same view in Night theme.
- `overview-mobile-375.png` — overview at 375px.
- `report-inspector-1024.png` — selected check record and raw JSON disclosure at 1024px.
- `history-1440.png` — saved local report history.
- `scan-setup-1440.png` — restricted local folder scan setup.
- `comparison-1440.png` — stored report comparison.

Fresh local commands run for this redesign:

```text
cd frontend
npm run format:check       # passed
npm run typecheck          # passed
npm test -- --reporter=dot # 14 passed
npm run build              # passed; bundled frontend assets regenerated
npm run test:browser       # 18 passed

cd ..
uv run --extra ui pytest -q # 630 passed, 1 skipped; existing Starlette deprecation warning
```

The browser suite covered 375, 390, 768, 1024, 1280, and 1440px viewports, axe checks, Paper/Night themes, keyboard/coarse-pointer operation, malicious text escaping, scan and cancellation, all decisions, import/export, history, and comparison. `git diff --check` passed. Hosted CI has not been run for this uncommitted visual redesign.
