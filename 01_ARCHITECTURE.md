# ModelVet — System Design

Detailed mechanical design. Companion to `01_ARCHITECTURE.md` (the "what and why") — this is the "exactly how."

## 1. Repository Structure

```
modelvet/
├── pyproject.toml
├── alembic.ini
├── README.md
├── .github/workflows/
│   ├── ci.yml                     # lint, type-check, unit+integration tests
│   └── eval-gate.yml              # meta-eval regression gate (enforced from V3, advisory in V1/V2)
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── configs/
│   ├── settings.dev.yaml
│   └── settings.prod.yaml
├── scripts/
│   ├── seed_gold_set.py           # loads gold_set_labels; supports the 10→20→40→60 staged growth
│   ├── run_leaderboard.py         # V3
│   └── replay_verdict.py          # re-run a stored evidence pool through Judge/debate for debugging
├── docs/                          # this doc set, kept in-repo, not just delivered once
│   ├── 00_PRD.md
│   ├── 01_ARCHITECTURE.md
│   ├── 02_SYSTEM_DESIGN.md
│   ├── 03_EXECUTION_PLAN.md
│   ├── resume_metrics.md
│   └── architecture/ADR/
│       ├── ADR-001-orchestration-framework.md
│       ├── ADR-002-vector-store.md
│       ├── ADR-003-debate-vs-single-pass-mvp.md
│       └── ADR-004-job-queue.md
├── src/modelvet/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── vet.py             # POST /vet, GET /vet/{job_id}          — V1
│   │           ├── verdicts.py        # GET /verdicts/{repo_id}                — V1
│   │           ├── watch.py           # POST/DELETE /watch/{repo_id}           — V2
│   │           ├── leaderboard.py     # GET /leaderboard                       — V3
│   │           ├── ask.py             # POST /ask                              — V3
│   │           └── health.py
│   ├── core/
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── middleware.py
│   ├── domain/
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   └── events.py
│   ├── services/
│   │   ├── vetting_service.py
│   │   ├── watch_service.py           # V2
│   │   └── leaderboard_service.py     # V3
│   ├── repositories/
│   │   ├── model_repository.py
│   │   ├── verdict_repository.py
│   │   └── evidence_repository.py
│   ├── agents/
│   │   ├── graph.py                   # state graph wiring; V1 wires Harvester→License/Community→Judge only
│   │   ├── state.py
│   │   ├── harvester.py
│   │   ├── license_agent.py
│   │   ├── benchmark_agent.py         # V2
│   │   ├── community_agent.py
│   │   ├── advocate.py                # V2
│   │   ├── skeptic.py                 # V2
│   │   └── judge.py                   # V1: reads evidence pool directly. V2: synthesizes debate instead
│   ├── prompts/
│   │   ├── harvester.md
│   │   ├── license_agent.md
│   │   ├── benchmark_agent.md         # V2
│   │   ├── community_agent.md
│   │   ├── advocate.md                # V2
│   │   ├── skeptic.md                 # V2
│   │   └── judge.md                   # two variants: judge_single_pass.md (V1), judge_debate.md (V2)
│   ├── rag/
│   │   ├── ingestion.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   ├── evaluation/
│   │   ├── component_evals/
│   │   │   ├── extraction_eval.py     # V2 (no benchmark agent to eval in V1)
│   │   │   ├── rag_eval.py            # V1
│   │   │   └── license_eval.py        # V1
│   │   ├── meta_eval/
│   │   │   ├── gold_set.py
│   │   │   ├── scorer.py
│   │   │   └── ablation.py            # V2 — needs both debate and single-pass modes to exist
│   │   ├── ci_gates/
│   │   │   └── deepeval_suite.py      # advisory V1/V2, blocking V3
│   │   └── promptfoo/
│   │       └── injection_tests.yaml   # V1 — this is security-critical, not deferred
│   ├── observability/
│   │   ├── tracing.py
│   │   ├── metrics.py
│   │   └── alerting.py                # drift alerts are V2; low-confidence routing alerting is V1
│   ├── security/
│   │   ├── prompt_injection_guard.py  # V1 — non-negotiable, ships with the Community agent from day one
│   │   ├── ssrf_guard.py              # V1
│   │   └── secrets.py
│   ├── schemas/
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── agent_io.py
│   ├── workers/
│   │   ├── worker_app.py
│   │   ├── vet_worker.py
│   │   └── scheduler.py               # V2
│   └── db/
│       ├── models.py
│       ├── session.py
│       └── migrations/
└── tests/
    ├── unit/
    ├── integration/
    ├── agents/
    ├── api/
    └── evaluation/
```

Note the versioning discipline baked into the tree itself: `prompt_injection_guard.py` and the Promptfoo suite are V1, not deferred — security on the untrusted-input path doesn't get MVP-cut. Everything else follows the PRD's staged scope.

## 2. Database Design

| Table | Key columns | V |
|---|---|---|
| `models` | `id`, `repo_id` (unique), `first_seen_at`, `last_vetted_at` | V1 |
| `vet_runs` | `id`, `model_id` FK, `status`, `started_at`, `completed_at`, `cost_usd`, `debate_enabled` (bool — powers the V2 ablation) | V1 |
| `evidence_items` | `id`, `vet_run_id` FK, `source_type`, `raw_text`, `url`, `content_hash` | V1 |
| `verdicts` | `id`, `vet_run_id` FK, `label`, `confidence`, `caveats` (jsonb), `published_at` | V1 |
| `debate_turns` | `id`, `vet_run_id` FK, `role`, `content`, `token_count` | V2 |
| `watch_schedules` | `id`, `model_id` FK, `cron_expr`, `is_active` | V2 |
| `alerts` | `id`, `model_id` FK, `alert_type`, `payload`, `sent_at` | V2 |
| `gold_set_labels` | `id`, `repo_id`, `human_label`, `rationale`, `labeled_at`, `batch` (10/20/40/60) | V1, grows over time |
| `eval_runs` | `id`, `run_type`, `metrics` (jsonb), `git_sha`, `created_at` | V1 |
| `audit_log` | `id`, `actor`, `action`, `entity`, `entity_id`, `at` | V1 |

`verdicts` and `models` are append-only-preferred — a re-vet creates a new `vet_runs` row rather than mutating history, which is what makes drift monitoring (V2) possible without redesigning storage later.

## 3. Vector Store Design (pgvector)

```
document_embeddings
  id            uuid
  vet_run_id    uuid FK
  source_type   text
  chunk_text    text
  chunk_index   int
  embedding     vector(1024)   -- bge-m3
  created_at    timestamptz
```

- Chunking: ~512 tokens, 15% overlap for cards/READMEs; one chunk per comment for discussion threads.
- Retrieval: cosine top-20 → `bge-reranker-v2-m3` down to top-5 before it reaches the Community agent's context.
- Caching: `content_hash` skips re-embedding unchanged source text.
- Hybrid search (V2+): add a `tsvector` column for exact-term matches like CVE IDs — pure semantic search misses identifiers.

## 4. API Design

| Endpoint | Method | V | Purpose |
|---|---|---|---|
| `/api/v1/vet` | POST | V1 | `{repo_id}` → enqueue, returns `{job_id, status}` |
| `/api/v1/vet/{job_id}` | GET | V1 | Poll status/result |
| `/api/v1/verdicts/{repo_id}` | GET | V1 | Latest published verdict |
| `/api/v1/watch` | POST | V2 | Add scheduled re-vetting |
| `/api/v1/watch/{repo_id}` | DELETE | V2 | Stop tracking |
| `/api/v1/leaderboard` | GET | V3 | Ranked trust leaderboard |
| `/api/v1/ask` | POST | V3 | Interactive QA over a model's evidence pool |
| `/api/v1/health` | GET | V1 | Liveness/readiness |

API-key auth, per-key rate limiting, Pydantic request/response models, standard error envelope (`{error_code, message, detail}`). `/vet` is async by design — cold runs can take up to 2 minutes.

## 5. Security Design

- **Prompt injection**: Community agent output passes through `prompt_injection_guard.py` before entering the shared evidence pool. Promptfoo runs adversarial injection attempts against this node in CI, starting V1.
- **SSRF**: `ssrf_guard.py` allowlists domains (huggingface.co, github.com, arxiv.org, osv.dev) before any outbound fetch the Harvester makes.
- **Secrets**: env-var + platform secrets store, centralized access via `secrets.py`.
- **Rate limiting**: per-API-key limits on `/vet`; internal backoff against HF/GitHub/OSV.dev.
- **Dependency/container security**: `pip-audit` in CI, non-root Docker user, minimal base image, Dependabot.
- **Logging**: structured logs carry IDs and status, never raw API keys or full evidence text.
- **SQL injection**: SQLAlchemy ORM throughout, no raw string SQL.

## 6. Evaluation Architecture

- **Component-level**: RAG faithfulness/relevancy/precision/recall (Ragas, floors 0.75/0.8/0.7/0.8) and license-classification accuracy — V1. Benchmark extraction precision/recall — V2, once the Benchmark agent exists.
- **Meta-eval**: `scorer.py` checks verdicts against the gold set, starting at 10 labels in V1, growing to 20→40 in V2 and 60 in V3.
- **Ablation** (V2): debate-on vs. debate-off on identical evidence — this is only possible once both Judge modes exist, which is exactly why it's a V2 deliverable, not V1.
- **CI gating**: advisory (reported, not blocking) in V1/V2; DeepEval assertions become a hard merge-blocker in V3 once the eval harness itself is trusted.

## 7. Observability

- Langfuse span per agent node (input, output, latency, tokens, cost) — V1.
- Cost-per-verdict and per-node latency as first-class metrics — V1.
- Content-hash caching — V1.
- Drift monitoring on watched models — V2.
- Prompt versioning via git-tracked `prompts/*.md`, gated by meta-eval — advisory V1/V2, enforced V3.
- Low-confidence verdicts route to a human-review queue instead of auto-publishing — V1.