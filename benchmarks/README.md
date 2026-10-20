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
