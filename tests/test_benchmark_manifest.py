import hashlib
import json
import os
from pathlib import Path

import pytest

from modelvet.benchmarks.corpus import (
    MAX_MANIFEST_BYTES,
    CorpusManifest,
    fixture_bytes,
    load_manifest,
    materialize,
    static_oracle,
)
from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "benchmarks/manifest.json"


def test_frozen_corpus_provenance_and_separate_oracles():
    corpus = load_manifest(MANIFEST)
    assert len(corpus.cases) == 10
    assert corpus.holdout_status == "NOT_SUPPLIED" and corpus.independent_review_status == "PENDING"
    for case in corpus.cases:
        assert case.adjudication == "METHOD_CHECKED_NOT_INDEPENDENT_REVIEW"
        assert case.label == static_oracle(case.recipe, fixture_bytes(case.recipe))
    source = (ROOT / "src/modelvet/benchmarks/corpus.py").read_text()
    assert "modelvet.structural" not in source and "pickle.load" not in source
    assert "extractall(" not in source and "from_pretrained" not in source


@pytest.mark.parametrize("case_index", range(10))
def test_materialized_bytes_identity_and_modes(tmp_path, case_index):
    case = load_manifest(MANIFEST).cases[case_index]
    target = tmp_path / "fixture"
    materialize(case, target)
    assert target.stat().st_mode & 0o777 == 0o700
    for file in case.files:
        path = target / file.relpath
        assert hashlib.sha256(path.read_bytes()).hexdigest() == file.sha256
        assert path.stat().st_mode & 0o777 == 0o600
    source = InputGate().validate(target, tmp_path / "reports", ScanLimits())
    with Snapshotter().create(source) as snapshot:
        assert InventoryService().collect(snapshot).manifest_digest == case.artifact_digest
    with pytest.raises(InvalidInput):
        materialize(case, target)


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "path",
        "label",
        "duplicate",
        "holdout",
        "review",
        "license",
        "recipe",
        "generator",
        "eligibility",
    ],
)
def test_manifest_tampering_cannot_create_truth(tmp_path, mutation):
    data = json.loads(MANIFEST.read_bytes())
    case = data["cases"][0]
    if mutation == "hash":
        case["files"][0]["sha256"] = "a" * 64
    elif mutation == "path":
        case["files"][0]["relpath"] = "../escape"
    elif mutation == "label":
        case["label"] = "MALFORMED_STRUCTURE"
    elif mutation == "duplicate":
        data["cases"].append(case)
    elif mutation == "holdout":
        case["split"] = "heldout"
    elif mutation == "review":
        data["independent_review_status"] = "COMPLETE"
    elif mutation == "license":
        case["license"] = "unknown"
    elif mutation == "recipe":
        case["recipe"] = "run-untrusted-script"
    elif mutation == "generator":
        data["generator_sha256"] = "a" * 64
    else:
        case["baseline_eligibility"] = "STANDALONE_PICKLE"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data))
    with pytest.raises(InvalidInput):
        load_manifest(path)


@pytest.mark.parametrize(
    "raw", [b"{}", b"[]", b"not-json", b'{"x":1,"x":2}', b"[" * 65 + b"]" * 65]
)
def test_invalid_manifest(tmp_path, raw):
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    with pytest.raises(InvalidInput):
        load_manifest(path)


def test_manifest_file_boundaries(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_bytes(MANIFEST.read_bytes())
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(InvalidInput):
        load_manifest(link)
    link.unlink()
    os.link(path, link)
    with pytest.raises(InvalidInput):
        load_manifest(path)
    link.unlink()
    path.write_bytes(b"")
    with path.open("wb") as stream:
        stream.truncate(MAX_MANIFEST_BYTES + 1)
    with pytest.raises(InvalidInput):
        load_manifest(path)
    assert not (tmp_path / "escape").exists()


def test_schema_export():
    assert CorpusManifest.model_json_schema() == json.loads(
        (ROOT / "schemas/benchmark-corpus-v1.json").read_text()
    )
