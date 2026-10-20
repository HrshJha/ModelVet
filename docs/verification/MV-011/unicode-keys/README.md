# MV-011 Unicode object-key correction

Date: 2026-10-20. Local macOS arm64, Python 3.12.15, uv 0.13.3.

## Reproduction and scope

Direct Python construction of `CheckRecord.details` and
`DependencyRecord.advisories` accepted unpaired-surrogate object keys. The
pinned serializer changed the high-surrogate key U+D800 into three U+FFFD
replacement characters. JSON input already rejected these keys. This is an
evidence validation correction; no admission bypass is established.

The shared validator now checks UTF-8 encoding of each object key while
retaining value validation and existing structural budgets. Eighteen added
cases cover high/low surrogates at the root, in objects and arrays, both
record types, JSON rejection, and valid accented/astral keys surviving a
serialization round trip. All fixture values are inert strings.

## Actual verification

- `uv run pytest -q tests/test_evidence.py` before the source correction:
  **12 failed, 28 passed**, exit 1 (`before-fix.txt`).
- The same command after the source correction: **40 passed**, exit 0
  (`after-fix.txt`).
- `local-gate.log` records lock, lint, formatting, security lint, mypy,
  full tests (**577 passed, one Linux-only skip**), wheel/sdist build, and
  fresh installed-package release checks (**10 passed**). Every command
  exited 0. The full suite builds its own fresh candidate offline.
- `final-gate.log` repeats the gates after the documentation updates.
- `identities.json` records base commit, changed source/test identities,
  dependency lock, schemas and final candidate distribution hashes.

Manual diff review: application change is confined to nested JSON key
validation. No dependency, schema shape, scanner invocation, admission
precedence or loader capability changes. The v1 data-model contract is
clarified, and all ADRs remain Proposed. Local checks do not supply
independent release/security review, benchmark adjudication, or Linux/KVM
loader prerequisites. Hosted results must be checked on the new PR.
