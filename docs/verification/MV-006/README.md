# PH-02 gate — 2026-10-20

MV-003–006 completed on macOS arm64/Python 3.12.15. Base `e2f2bb2`, implementation uncommitted. Task logs are in their corresponding MV directories. Full suite: 81 passed; lint/format, mypy, lock check and isolated build exit 0. The first MV-006 type check required an explicit enum annotation; its output is retained.

Coverage includes path/output separation, no symlink ancestors, hardlinks/FIFO/symlink rejection, private snapshot permissions and cleanup, byte/entry caps, mutation during copy, root replacement, canonical identity and Hypothesis ordering/content properties, source additions/deletions/renames/changes, snapshot drift, bounded classification, deceptive suffixes, unknown formats and changed snapshot paths. Snapshot rechecks reuse the same bounded observer without an extra disk copy.

No model deserialization or source-code import occurs. These tests establish the listed behaviors on this host, not atomic filesystem isolation or Linux compatibility. Empty directories do not enter manifest-v1 identity. Classification only establishes applicability; no structural validation, scanner, policy or report pipeline is implemented yet. CLI valid scans still fail explicitly with 50.
