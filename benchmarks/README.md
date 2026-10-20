# Synthetic development corpus

Ten inert, deterministic recipes exercise static evidence contracts. This is development data, not an independently reviewed or hidden benchmark. All bytes are generated locally under the repository MIT license. No third-party weights, payloads or executable malicious samples are included.

`manifest.json` freezes generator SHA-256, per-file hashes/sizes, artifact identity, static labels, method and baseline eligibility. Loading recomputes all bytes, verifies labels with alternative stdlib methods and rejects tampering. The oracles use struct/json, ZipFile indexes and pickletools opcode inspection; they do not call ModelVet structural inspectors, deserialize pickle or extract archives. Same-author method checks are explicitly not independent human adjudication.

## Cases and limits

- Safetensors valid/truncated headers; ZIP index valid/unsafe member name.
- Pickle None, integer and truncated inert opcode streams, all statically inspected.
- Comment-only source presence, conflicting license declarations and unknown bytes.
- ModelScan comparison eligibility is restricted to standalone pickle cases. Other cases are NOT_APPLICABLE to the configured baseline, never counted as misses.
- Every case is development-only. Hidden holdout and independent review remain pending. The manifest parser refuses to relabel these cases as held out or reviewed.

The freeze command `uv run python benchmarks/freeze_manifest.py` exclusively creates a new manifest; it refuses overwrite. A generator change invalidates the current manifest. Preserve the old manifest/results, review the change, then deliberately freeze a new corpus version. Do not regenerate labels after looking at held-out outcomes.

Run `uv run pytest -q tests/test_benchmark_manifest.py`. No fixture bytes are executed. The manifest and safe generator are shipped with the source archive; experiment operational reports/raw output should remain private and outside the source archive.

## Executable development pilot

After separately installing ModelScan as documented in tools/modelscan/README.md:

```sh
PATH="$PWD/.scanner-venv/bin:$PATH" uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out out/my-new-pilot --repeats 2
```

The output directory must be new. Exit **30** is the explicit INCONCLUSIVE study result, not a failed shell invocation or an admission verdict. Use `--help` for finite repeat/timeout arguments; invalid data/arguments are 40, orchestration errors 50, interruption 130. Completed result.json is written last; on failure, private partial evidence may remain without a completed result marker. ModelScan and ModelVet receive the same frozen fixture identity and timeout ceiling. Their pipelines are timed independently and measure different work; no speed ratio or comparative overhead is reported.

Results contain raw digest references and version/configuration observations. Raw vendor output may retain private temporary paths. Preserve the complete private output; a sanitized local pilot summary is retained in results/. No external baseline executable is accepted through manifest data. Alternative tools are NOT_RUN unless a separately reviewed adapter/configuration exists. No superiority claim, hidden holdout or independent adjudication is manufactured by the runner.
