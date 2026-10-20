# MV-023 local pilot and later-phase readiness — 2026-10-20

macOS arm64/Python 3.12.15/uv 0.13.3; no third-party dependency addition. Work started at e2f2bb269683d79cd6a12757aa140357fef089ad. Checkpoint af86ffee5c7b4f1e990e9dbbdba6625e973acef0 appeared outside agent commands during this turn and was preserved. A later external checkpoint b91a791c6c3b4137a39fb540822e888d54948549 was observed; final source/worktree identities are in experiment.json/artifacts.json; no agent commit/push/tag/publication.

## Executed checks

- task-initial.log: initial 19 metrics/runner cases pass.
- targeted.log: `uv run pytest -q tests/test_benchmark_manifest.py tests/test_benchmark_metrics.py tests/test_release.py`, exit 0, 60 pass (28 manifest, 23 metrics/runner, 9 fresh-install release cases).
- gate-initial.log: earlier 481 pass / one Linux-only skip.
- gate.log: final command below, exit 0, 486 pass / one Linux-only skip; lock/lint/format/security/types pass, 51 source files.
- initial-lint.log, initial-types.log, intermediate-types.log and gate-lint-failed.log retain intermediate line-length/type errors; corrected before the successful gate.

```sh
uv lock --check &&
uv run ruff check . &&
uv run ruff format --check . &&
uv run ruff check src --select S &&
uv run mypy src &&
uv run pytest -q
```

completion.log records `uv run pytest -q tests/test_release.py tests/test_docs_contract.py`: exit 0, 12 pass after status updates. build.log records the subsequent `uv build`. artifacts.json records both archive hashes and contents; whitespace-review.json records tracked and no-index checks. Source archives ship corpus schema/manifest/safe generator but exclude operational results/raw output.

## Actual experiment

```sh
PATH="$PWD/.scanner-venv/bin:$PATH" uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out out/development-pilot-20261020 --repeats 2
```

pilot-command.log: actual exit 30 (expected), INCONCLUSIVE, 40 observations on ten inert recipes/two repeats. Six joint eligible input-context observations; fourteen baseline observations NOT_APPLICABLE. Actual pinned ModelScan is 0.8.8; scanner-environment.json records its observed Python/package versions. No model loading or realistic malicious payloads. Results/raw metadata remain private in ignored out/development-pilot-20261020; sanitized summary in benchmarks/results/. experiment.json records result/context/source hashes and private evidence validation.

There are no independently adjudicated discrepancy positives or hidden holdout, so no efficacy/error rates or intervals are reported. Same-author static method labels are not independent human review. ModelVet policy decisions and scanner file assessments are different predicates. Other tools are NOT_RUN; no efficacy/support conclusion about them follows.

## Later phase prerequisites

loader-readiness.json records current Darwin arm64, absent KVM/Firecracker/jailer and no supplied dedicated Linux host/independent review/holdout. Proposed review packet ../../LOADER_REVIEW_PACKET.md enables no capability and does not complete MV-030. User explicitly selected leaving these gates pending while finishing local validation. PH-08 research acceptance, PH-11 execution, hosted CI and public release remain pending.
