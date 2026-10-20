"""T-OSV-01: only explicit, attributable offline evidence can complete this check."""

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from fixture_factory import artifact
from test_cli import invoke

from modelvet.core.errors import InvalidInput
from modelvet.dependencies.advisories import (
    MAX_SNAPSHOT_BYTES,
    AdvisoryDocument,
    AdvisoryReader,
    load_snapshot,
)
from modelvet.dependencies.manifest import DependencyDeclaration

NOW = "2026-10-20T12:00:00Z"
DIGEST = "sha256:" + "a" * 64
DEPENDENCY = DependencyDeclaration(
    "Demo_Package",
    "PyPI",
    "1.0.0",
    "b" * 64 + "#json:/dependencies/0",
    "c" * 64,
    "DECLARED_PINNED",
)


def osv(**updates):
    return {
        "schema_version": "1.9.2",
        "id": "x_MODELVET-SYNTHETIC-1",
        "modified": NOW,
        "affected": [
            {"package": {"name": "demo-package", "ecosystem": "PyPI"}, "versions": ["1.0.0"]}
        ],
        **updates,
    }


def envelope(vulns=None):
    return {
        "schema_version": "1.0.0",
        "generated_at": NOW,
        "source": "local-synthetic-example",
        "queries": [
            {
                "package": {"name": "demo.package", "ecosystem": "PyPI"},
                "version": "1.0.0",
                "complete": True,
                "response": {"vulns": [osv()] if vulns is None else vulns},
            }
        ],
    }


def save(tmp_path, data=None):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(envelope() if data is None else data))
    return path


def assess(path, dependencies=(DEPENDENCY,), **options):
    return AdvisoryReader().assess(
        dependencies,
        snapshot_path=path,
        artifact_digest=DIGEST,
        report_digest=DIGEST,
        **{"as_of": NOW, **options},
    )


def test_explicit_match_is_not_exploitability(tmp_path):
    path = save(tmp_path)
    result = assess(path)
    (row,) = result.dependencies
    assert row.status == "COMPLETE" and row.result == "AFFECTED_VERSION"
    assert result.exit_code == 30 and not result.admission_recomputed
    assert result.snapshot_digest == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    assert row.matches[0].source_ref.endswith("#/queries/0/response/vulns/0")
    assert row.dependency_source_ref == DEPENDENCY.source_ref
    assert "exploitability" in " ".join(result.limitations)
    assert not hasattr(result, "decision")


@pytest.mark.parametrize(
    "records",
    [
        [],
        [
            osv(
                affected=[
                    {
                        "package": {"name": "Demo_Package", "ecosystem": "PyPI"},
                        "versions": ["0.9.0"],
                    }
                ]
            )
        ],
        [osv(withdrawn=NOW)],
    ],
)
def test_fresh_query_no_match_is_scoped(tmp_path, records):
    result = assess(save(tmp_path, envelope(records)))
    assert result.status == "COMPLETE" and result.exit_code == 0
    assert result.dependencies[0].result == "NO_MATCH_IN_SNAPSHOT"


@pytest.mark.parametrize("as_of", ["2026-10-28T12:00:01Z", "2026-10-19T12:00:00Z"])
def test_stale_or_future_keeps_matches_but_cannot_complete(tmp_path, as_of):
    result = assess(save(tmp_path), as_of=as_of)
    assert result.status == "INCONCLUSIVE" and result.exit_code == 30
    assert result.dependencies[0].matches
    assert result.dependencies[0].result == "AFFECTED_VERSION"


def test_age_boundary_and_missing_optional_snapshot(tmp_path):
    path = save(tmp_path, envelope([]))
    assert assess(path, as_of="2026-10-27T12:00:00Z").status == "COMPLETE"
    assert assess(path, as_of="2026-10-27T12:00:01Z").exit_code == 30
    assert assess(None).status == "NOT_RUN" and assess(None).exit_code == 30
    assert assess(None, required=False).exit_code == 0
    assert assess(path, dependencies=()).status == "INCONCLUSIVE"
    assert assess(path, dependencies=()).exit_code == 30


@pytest.mark.parametrize(
    "variant",
    [
        "missing-query",
        "different-version",
        "partial",
        "page",
        "ranges",
        "ecosystem",
        "schema",
        "no-versions",
        "wrong-package",
    ],
)
def test_incomplete_proof_never_completes(tmp_path, variant):
    data = envelope([])
    query = data["queries"][0]
    if variant == "missing-query":
        data["queries"] = []
    elif variant == "different-version":
        query["version"] = "1.0"
    elif variant == "partial":
        query["complete"] = False
    elif variant == "page":
        query["response"]["next_page_token"] = "untrusted-page-token"
    else:
        record = osv()
        item = record["affected"][0]
        if variant == "ranges":
            item["ranges"] = [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}]}]
        elif variant == "ecosystem":
            item["ecosystem_specific"] = {"platform": "not-evaluated"}
        elif variant == "schema":
            record["schema_version"] = "2.0.0"
        elif variant == "no-versions":
            item["versions"] = []
        elif variant == "wrong-package":
            item["package"]["name"] = "unrelated"
        query["response"]["vulns"] = [record]
    result = assess(save(tmp_path, data))
    assert result.status == "INCONCLUSIVE" and result.exit_code == 30
    assert result.dependencies[0].result != "NO_MATCH_IN_SNAPSHOT"


@pytest.mark.parametrize(
    "dependency",
    [
        replace(DEPENDENCY, ecosystem="npm"),
        replace(DEPENDENCY, version=None),
        replace(DEPENDENCY, version="*"),
        replace(DEPENDENCY, status="INCONCLUSIVE"),
    ],
)
def test_unresolved_dependency_not_promoted(tmp_path, dependency):
    result = assess(save(tmp_path, envelope([])), dependencies=(dependency,))
    assert result.status == "INCONCLUSIVE" and result.dependencies[0].status == "UNSUPPORTED"
    assert result.exit_code == 30


def test_duplicate_dependencies_and_deterministic_order(tmp_path):
    path = save(tmp_path)
    other = replace(DEPENDENCY, name="other")
    assert (
        assess(path, dependencies=(DEPENDENCY, other)).semantic_digest
        == assess(path, dependencies=(other, DEPENDENCY)).semantic_digest
    )
    duplicates = assess(path, dependencies=(DEPENDENCY, replace(DEPENDENCY, name="demo-package")))
    assert duplicates.exit_code == 30
    assert all(r.status == "INCONCLUSIVE" for r in duplicates.dependencies)
    first = assess(path)
    assert first.semantic_digest == assess(path).semantic_digest
    assert first.semantic_digest != assess(path, required=False).semantic_digest


@pytest.mark.parametrize(
    "mutation",
    [
        "schema",
        "timestamp",
        "unknown",
        "duplicate-query",
        "duplicate-id",
        "postdate",
        "complete-string",
        "id-injection",
    ],
)
def test_invalid_snapshot_is_controlled(tmp_path, mutation):
    data = envelope()
    if mutation == "schema":
        data["schema_version"] = "2.0.0"
    elif mutation == "timestamp":
        data["generated_at"] = "2026-10-20"
    elif mutation == "unknown":
        data["download_url"] = "https://never-fetched.invalid"
    elif mutation == "duplicate-query":
        data["queries"] *= 2
    elif mutation == "duplicate-id":
        data["queries"][0]["response"]["vulns"] *= 2
    elif mutation == "postdate":
        data["queries"][0]["response"]["vulns"][0]["modified"] = "2027-01-01T00:00:00Z"
    elif mutation == "complete-string":
        data["queries"][0]["complete"] = "true"
    else:
        data["queries"][0]["response"]["vulns"][0]["id"] = "<script>"
    with pytest.raises(InvalidInput):
        assess(save(tmp_path, data))


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json",
        b'{"schema_version":"1.0.0","schema_version":"1.0.0"}',
        b'{"value":NaN}',
        b"[" * 65 + b"]" * 65,
    ],
)
def test_malformed_json(tmp_path, raw):
    path = tmp_path / "snapshot.json"
    path.write_bytes(raw)
    with pytest.raises(InvalidInput):
        load_snapshot(path)


def test_file_safety_budgets_and_no_network(tmp_path, monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("Network attempted")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    path = save(tmp_path)
    assert assess(path).status == "COMPLETE"
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(InvalidInput):
        load_snapshot(link)
    link.unlink()
    os.link(path, link)
    with pytest.raises(InvalidInput):
        load_snapshot(path)
    link.unlink()
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(InvalidInput):
        load_snapshot(fifo)
    path.write_bytes(b"")
    with path.open("wb") as stream:
        stream.truncate(MAX_SNAPSHOT_BYTES + 1)
    with pytest.raises(InvalidInput):
        load_snapshot(path)


@pytest.mark.parametrize("value", [-1, 366, True])
def test_age_validation(tmp_path, value):
    with pytest.raises(InvalidInput):
        assess(save(tmp_path), max_age_days=value)


def test_schema_matches_exported_model():
    root = Path(__file__).parents[1]
    assert AdvisoryDocument.model_json_schema() == json.loads(
        (root / "schemas/advisories-v1.json").read_text()
    )


def test_cli_supplement_preserves_report_and_redacts_snapshot_source(tmp_path):
    root = artifact(tmp_path / "model")
    (root / "modelvet-environment.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "dependencies": [{"name": "demo-package", "ecosystem": "PyPI", "version": "1.0.0"}],
            }
        )
    )
    out = tmp_path / "reports"
    scan = invoke("scan", str(root), "--out", str(out), "--json-summary")
    assert scan.returncode == 0, scan.stderr
    report = out / json.loads(scan.stdout)["report"]
    original = report.read_bytes()
    data = envelope()
    data["source"] = "https://user:sentinel-secret@example.invalid/private"
    path = save(tmp_path, data)
    result = invoke("advisories", str(report), "--snapshot", str(path), "--as-of", NOW)
    assert result.returncode == 30, result.stderr
    evidence = json.loads(result.stdout)
    assert evidence["assessment"]["admission_recomputed"] is False and evidence["exit_code"] == 30
    AdvisoryDocument.model_validate_json(result.stdout)
    assert "sentinel-secret" not in result.stdout + result.stderr
    assert str(tmp_path) not in result.stdout + result.stderr
    assert report.read_bytes() == original
    result = invoke("advisories", str(report), "--as-of", NOW)
    assert (
        result.returncode == 30 and json.loads(result.stdout)["assessment"]["status"] == "NOT_RUN"
    )
    result = invoke("advisories", str(report), "--as-of", NOW, "--optional")
    assert result.returncode == 0 and json.loads(result.stdout)["assessment"]["status"] == "NOT_RUN"
    path.write_text("bad-json")
    result = invoke("advisories", str(report), "--snapshot", str(path), "--as-of", NOW)
    assert result.returncode == 40 and result.stdout == ""
    assert "Traceback" not in result.stderr


def test_declared_complete_does_not_override_missing_record_semantics(tmp_path):
    data = envelope([osv(affected=[])])
    assert assess(save(tmp_path, data)).exit_code == 30
    # An explicit empty complete query is a scoped no-match assertion, not a global feed claim.
    data = envelope([])
    data["queries"][0]["complete"] = False
    assert assess(save(tmp_path, data), required=False).dependencies[0].result == "UNKNOWN"


def test_snapshot_read_identity_drift(tmp_path, monkeypatch):
    from modelvet.dependencies import advisories

    original = advisories.stat_identity
    calls = 0

    def changed(info):
        nonlocal calls
        calls += 1
        return (*original(info), calls)

    monkeypatch.setattr(advisories, "stat_identity", changed)
    with pytest.raises(InvalidInput, match="changed"):
        load_snapshot(save(tmp_path))


@pytest.mark.parametrize("variant", ["queries", "records", "symlink-parent", "missing"])
def test_other_input_boundaries(tmp_path, variant):
    data = envelope()
    if variant == "queries":
        data["queries"] *= 1001
    elif variant == "records":
        data["queries"][0]["response"]["vulns"] *= 1001
    elif variant == "missing":
        with pytest.raises(InvalidInput):
            load_snapshot(tmp_path / "absent.json")
        return
    path = save(tmp_path, data)
    if variant == "symlink-parent":
        (tmp_path / "alias").symlink_to(tmp_path, target_is_directory=True)
        path = tmp_path / "alias" / path.name
    with pytest.raises(InvalidInput):
        load_snapshot(path)


def test_document_rejects_tampered_digest_and_exit(tmp_path):
    from pydantic import ValidationError

    document = AdvisoryDocument.from_assessment(assess(save(tmp_path)))
    assert document == AdvisoryDocument.model_validate_json(document.model_dump_json())
    for field, value in [("semantic_digest", DIGEST), ("exit_code", 0)]:
        data = document.model_dump(mode="json")
        data[field] = value
        with pytest.raises(ValidationError):
            AdvisoryDocument.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "field,value", [("status", "COMPLETE"), ("snapshot_generated_at", None), ("max_age_days", -1)]
)
def test_assessment_rejects_inconsistent_completeness(tmp_path, field, value):
    from pydantic import ValidationError

    from modelvet.dependencies.advisories import AdvisoryAssessment

    data = assess(save(tmp_path), as_of="2026-11-01T00:00:00Z").model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        AdvisoryAssessment.model_validate_json(json.dumps(data))


def test_conflicting_advisory_identity_across_queries(tmp_path):
    import copy

    data = envelope()
    other = copy.deepcopy(data["queries"][0])
    other["version"] = "2.0.0"
    other["response"]["vulns"][0]["affected"][0]["versions"] = ["2.0.0"]
    data["queries"].append(other)
    with pytest.raises(InvalidInput, match="Conflicting"):
        load_snapshot(save(tmp_path, data))
