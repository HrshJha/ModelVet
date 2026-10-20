# Benchmark plan — scanner coverage and loader interpretation

**Status:** study design only. No dataset downloaded, fixtures constructed, benchmark run, numeric rates calculated or competing tool superiority established. Primary purpose: **falsify** ModelVet's proposed incremental value if existing alternatives already handle the relevant cases.

## Research questions

- **RQ1:** On fixed local artifacts with known scanner applicability, does ModelVet surface more *independently confirmed* unassessed content than baseline tool status output?
- **RQ2:** When positive loader-access evidence is available in a controlled test, does a scanner mark security-relevant content unassessed that the loader can access?
- **RQ3 (P2 only):** For a fixed artifact and explicitly pinned framework versions, is security-relevant loading behavior demonstrably different across versions, and is this actionable beyond existing advisory checks?

**H1:** per-file coverage reconciliation reduces false-clean assessments over naive `exit=0/no-findings` interpretation. **H2 (higher bar):** it detects held-out, consequential discrepancies beyond contemporary tools. Both hypotheses could fail. H1 does not imply H2 or commercial superiority.

## Comparators and eligibility

- Baseline A: **ModelScan** exact pinned version and official JSON/exit status. Baseline B: **PickleBall** when pickle/library combination actually supported. Baseline C: **Layerfault** for documented supported formats if runnable and licensed for testing. Optional JFrog/Protect AI commercial comparators only if lawful access and consistent artifact scope is available.
- Don't compare a GGUF-only test to a pickle-only scanner as if unsupported were a miss. Comparisons are paired **only within jointly supported format/context**; otherwise state `NOT_APPLICABLE/UNSUPPORTED`.
- Log CLI command, scanner version, rule config, model fixture SHA-256, host OS, runtime, timeouts, report digest and tool availability. No commercial vendor claims without direct runs.

## Corpus plan (NOT yet created)

| Stratum | Type | Ground-truth procedure | Ordinary CI safety |
|---|---|---|---|
| S1 | Benign tiny metadata/safetensors headers | independently parse expected offsets/key sets | yes, pure bytes |
| S2 | Benign archive index and small pickle opcode *text fixtures* | two static parsers independently label reachable members, no unpickling | yes if inert |
| S3 | Malformed, truncated, duplicate and over-limit files | expected failure based on standards/stdlib behavior | yes |
| S4 | Controlled scanner stub skipped-file reports | fixture generator + independently written oracle | yes; not real malware |
| S5 | Published scanner/loader mismatch reference cases | reproduce carefully in isolated research environment with source/version log; no published payload by default | no if executable |
| S6 | Held-out unseen samples | two independent reviewers/methods; avoid training/tuning against them | safe only if inert |
| S7 (P2) | Loader-version controlled benign/adversarial behaviors | instrumented microVM trace and independent verification | never ordinary CI |

Dataset provenance per fixture: source link/license/access date, artifact SHA-256, generated method, expected loader version, adjudication notes, whether unsafe, whether usable publicly, and disclosure constraints. Control any realistic malicious samples outside default repo. Do not derive ground truth solely from ModelVet output or one competing tool.

## Technical scope / compatibility matrix

| Artifact | Static MVP | Baseline eligibility | P2 loader observation |
|---|---|---|---|
| `.safetensors` | bounded header and lengths | structural tools with documented support | selected Transformers later |
| `.pt/.pth` PyTorch ZIP | archive inventory + ModelScan | ModelScan, other pickle-aware tools if supported | isolated pinned PyTorch later |
| standalone pickle-like | scanner/structural classification | ModelScan/PickleBall only if supported | deferred unless safe harness |
| repo `.py` / custom loader | identify+policy, never import | static code tools if available | P2 only, explicit approval |
| GGUF | UNKNOWN/INSUFFICIENT unless explicitly supported | Layerfault or format-specific tools only | not initial target |
| TensorFlow/Keras | out of first supported matrix | comparator not penalized for noncoverage | not initial target |

## Measurement and formulas

Each dataset row has `fixture_id`, `support_status`, `ground_truth`, `tool_version`, `predicted_check_status`, `predicted_security_label`, `runtime_s`, `peak_rss_bytes`, `repeat_id`, `artifact_digest`, `adjudicator_id`.

- **False-clean rate:** `# cases the tool labels complete/no finding despite independently proven relevant unassessed content / # ground-truth discrepancy cases within supported domain` (also report denominator and confidence interval). If tool reports UNKNOWN/UNSUPPORTED correctly it is *not* a false clean.
- **Confirmed incremental discrepancy detection:** number of **unique independently adjudicated** missed assessments ModelVet identifies and *all applicable baselines* miss, normalized by jointly supported cases.
- **Benign false positive:** `# benign supported cases incorrectly BLOCKed or characterized malicious / # benign supported cases`; distinguish correct INSUFFICIENT on unsupported input from malicious FP.
- **Unsupported/partial rate:** separate percentage of cases with incomplete proof, so tools cannot improve FP by abstaining on everything.
- **Reproducibility:** runs agreeing on per-file coverage, decision and evidence digest / repeated trials, controlling tool versions.
- **Cost:** wall time, peak RSS, snapshot storage bytes, reviewer effort per confirmed finding; same hardware and resource ceilings.
- **Loader scope P2:** distinguish `observed_file_access`, `attempted_execution`, `observed_execution`, and `inferred_risk`—never aggregate them as all "RCE".

Report paired sample size and uncertainty; bootstrap interval or exact binomial interval when enough samples, otherwise raw counts only. Do not present numerical conclusions until run data and independently checked labels exist.

## Experimental procedure

1. Pre-register hypotheses, applicable formats, exact baselines, budget constraints and success/failure decision thresholds before examining held-out set.
2. Build corpus from benign generated fixtures and referenced security cases with separate safe handling; hash every artifact and record provenance.
3. Independently adjudicate ground truth using an alternative parser plus review of loader behavior where safe. Reviewer ideally blinded to tool output.
4. Freeze selected modelscan/other tool versions; run all relevant baselines and ModelVet under comparable resource/time settings; document any unsupported or unavailable tools.
5. Inspect discrepancies manually; reproduce each as a minimal harmless fixture where possible; exclude unverifiable claims from confirmed metric.
6. Hold out some cases until thresholds fixed; report favorable and unfavorable outcomes, failures, runtime and scope.
7. P2 trials only after VM security gate in `THREAT_MODEL.md`; no host execution.

## Decision criteria (proposed, subject to review)

- Continue exploring discrepancy differentiation only if **multiple independently confirmed held-out cases** demonstrate a materially actionable gap with acceptable false-positive and overhead trade-off vs eligible baselines. Do not impose invented numerical guarantees from zero data.
- Narrow or reject differentiated scanner/loader claim if all confirmed cases are already detected by strongest comparator, if positives require contrived unsupported formats, if costs dwarf the benefit, or if no independent ground truth is possible.
- If only H1 succeeds, present ModelVet as **coverage-accounting and policy integrity** rather than a superior malicious-model detector.

## Reproduction instructions (PLANNED)

```sh
uv sync --locked
uv run pytest -q tests/test_benchmark_manifest.py tests/test_benchmark_metrics.py
# After implementation and corpus review only:
uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out benchmarks/results/
```

The exact runner's flags are a **proposed contract**, not a verified command. Public results must include dataset hashes and tool versions, unknown counts, a methodology change log, and limitations. No scan output here proves a general "safe to load" property.
