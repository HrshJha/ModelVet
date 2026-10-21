# Hub feature acceptance — local candidate

Implemented CLI and Workbench URL scanning; current contract: [HUB_ASSESSMENT_SPEC](../../HUB_ASSESSMENT_SPEC.md). Evidence is local engineering validation, not independent certification or a new published release.

- `python-tests.log`: actual full suite, 732 passed / one platform skip; includes installed-package validation.
- `browser-tests.log`: actual 21-workflow Chromium suite. Component tests: 14 passed. Format/types/build, lock/lint/security/mypy/schema checks passed.
- `live-observation.json`: identities and complete retrieval inventory from a real Chrome UI scan of the public tiny-random-bert repository, no credential selected; nine files retrieved, one oversized, INSUFFICIENT. Reports are assertions about the exact bytes/checks, not a model safety certificate.
- `workbench-live-hf-form.png`: actual in-app preview, URL form ready.
- `hugging-face-setup-1440.png`, `hugging-face-setup-375.png`: synthetic browser acceptance captures.
- `hugging-face-report-1440.png`: an imported inert v2 fixture displaying a retrieval gap, not a live model outcome.
- `distributions.json`: final locally built wheel/source hashes and sizes. No publication is implied.

The official client 2.2.0 was evaluated but not installed; its source hashes and official links are in RESEARCH_REFERENCES. ModelVet uses the narrow stdlib transport described in the specification, with no new dependencies. Current source remains uncommitted; hosted execution/publication are pending. The previous published Mac preview has not acquired this feature retroactively.
