"""V1 policy syntax, closed rules, stable identity and bounded file loading."""

import json
import os
import subprocess
import sys
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest

from modelvet.core import config
from modelvet.core.config import MAX_POLICY_BYTES, PolicyValidator, load_policy
from modelvet.core.errors import InvalidInput
from modelvet.inventory.classify import APPLICABILITY_VERSION, FileFormat, applicable_checks
from modelvet.policies.models import CHECK_IDS, AdmissionDecision, Policy


def default_bytes() -> bytes:
    return files("modelvet.policies").joinpath("default.toml").read_bytes()


def render(data: dict) -> bytes:
    lines = []
    tables = []
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            tables.append((key, value))
        else:
            lines.append(f"{key} = {json.dumps(value)}")
    for key, rows in tables:
        for row in rows:
            lines.append(f"[[{key}]]")
            lines.extend(f"{k} = {json.dumps(v)}" for k, v in row.items())
    return ("\n".join(lines) + "\n").encode()


def controlled_data() -> dict:
    data = tomllib.loads(default_bytes().decode())
    data["controls"] = [{"control_id": "ISOLATED_LOADING", "owner": "Platform security"}]
    data["control_rules"] = [
        {"rule_id": "ISOLATE", "condition": "SERIALIZED_MODEL", "control_ids": ["ISOLATED_LOADING"]}
    ]
    return data


def test_default_is_conservative_versioned_and_complete() -> None:
    policy = load_policy()
    assert policy.schema_version == "1.0.0"
    assert policy.policy_id == "default-policy-v1"
    assert policy.applicability_version == APPLICABILITY_VERSION
    assert set(policy.mandatory_checks) == CHECK_IDS
    assert policy.optional_checks == ()
    assert policy.required_claims == ("LICENSE", "PROVENANCE")
    assert policy.prohibitions[0].category == "REPOSITORY_CODE"
    registry = {check for kind in FileFormat for check in applicable_checks(kind)}
    assert CHECK_IDS == registry | {"dependencies:declared"}


def test_comments_whitespace_field_and_rule_order_do_not_change_policy_hash() -> None:
    data = controlled_data()
    first = PolicyValidator().parse(render(data))
    data["mandatory_checks"].reverse()
    data["required_claims"].reverse()
    data = dict(reversed(list(data.items())))
    second = PolicyValidator().parse(b"# harmless comment\n\n" + render(data))
    assert first.semantic_digest == second.semantic_digest
    data["controls"][0]["owner"] = "Another owner"
    assert first.semantic_digest != PolicyValidator().parse(render(data)).semantic_digest


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_key",
        "unknown_schema",
        "missing_schema",
        "unknown_applicability",
        "unknown_check",
        "missing_mapping",
        "overlap",
        "optional_identity",
        "duplicate_check",
        "duplicate_rule",
        "reserved_rule",
        "duplicate_category",
        "unknown_category",
        "unknown_condition",
        "conflicting_rules",
        "unknown_control",
        "missing_control",
        "unused_control",
        "duplicate_control",
        "duplicate_condition",
        "duplicate_reference",
        "empty_owner",
        "control_owner_type",
        "owner_control_char",
        "unknown_claim",
        "duplicate_claim",
        "unknown_nested_key",
        "integer_version",
        "empty_rule_id",
    ],
)
def test_invalid_or_ambiguous_policies_are_rejected(mutation) -> None:
    data = controlled_data()
    match mutation:
        case "unknown_key":
            data["network"] = True
        case "unknown_schema":
            data["schema_version"] = "9.0.0"
        case "missing_schema":
            del data["schema_version"]
        case "unknown_applicability":
            data["applicability_version"] = "1"
        case "unknown_check":
            data["mandatory_checks"].append("imaginary:clean")
        case "missing_mapping":
            data["mandatory_checks"].remove("modelscan")
        case "overlap":
            data["optional_checks"] = ["modelscan"]
        case "optional_identity":
            data["mandatory_checks"].remove("identity")
            data["optional_checks"] = ["identity"]
        case "duplicate_check":
            data["mandatory_checks"].append("identity")
        case "duplicate_rule":
            data["control_rules"][0]["rule_id"] = data["prohibitions"][0]["rule_id"]
        case "reserved_rule":
            data["prohibitions"][0]["rule_id"] = "POLICY-APPROVE"
        case "duplicate_category":
            data["prohibitions"].append({"rule_id": "OTHER", "category": "REPOSITORY_CODE"})
        case "unknown_category":
            data["prohibitions"][0]["category"] = "MALWARE"
        case "unknown_condition":
            data["control_rules"][0]["condition"] = "always_true()"
        case "conflicting_rules":
            data["control_rules"][0]["condition"] = "REPOSITORY_CODE"
        case "unknown_control":
            data["controls"][0]["control_id"] = "DO_ANYTHING"
        case "missing_control":
            data["controls"] = []
        case "unused_control":
            data["control_rules"] = []
        case "duplicate_control":
            data["controls"] *= 2
        case "duplicate_condition":
            data["control_rules"].append({**data["control_rules"][0], "rule_id": "OTHER"})
        case "duplicate_reference":
            data["control_rules"][0]["control_ids"] *= 2
        case "empty_owner":
            data["controls"][0]["owner"] = " "
        case "control_owner_type":
            data["controls"][0]["owner"] = 42
        case "owner_control_char":
            data["controls"][0]["owner"] = "name\nterminal"
        case "unknown_claim":
            data["required_claims"] = ["LEGAL_CLEARANCE"]
        case "duplicate_claim":
            data["required_claims"] *= 2
        case "unknown_nested_key":
            data["controls"][0]["shell"] = "unsafe"
        case "integer_version":
            data["policy_version"] = 1
        case "empty_rule_id":
            data["prohibitions"][0]["rule_id"] = ""
    with pytest.raises(InvalidInput):
        PolicyValidator().parse(render(data))


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\xff",
        b"[",
        b"x = 1\nx = 2",
        b"x = nan",
        b"x = inf",
        b"x = 2026-10-20",
        b"x = " + b"[" * 2000 + b"0" + b"]" * 2000,
        b"x." * 100 + b"value=1",
        b"x=[" + b"0," * 4100 + b"]",
        b"#" * (MAX_POLICY_BYTES + 1),
    ],
)
def test_malformed_oversized_or_deep_toml_is_controlled(raw) -> None:
    with pytest.raises(InvalidInput):
        PolicyValidator().parse(raw)


def test_selected_policy_replaces_default_and_environment_cannot_override(
    tmp_path, monkeypatch
) -> None:
    data = controlled_data()
    data["policy_id"] = "selected"
    selected = tmp_path / "policy.toml"
    selected.write_bytes(render(data))
    monkeypatch.setenv("MODELVET_POLICY", "/nonexistent/unsafe.toml")
    assert load_policy().policy_id == "default-policy-v1"
    assert load_policy(selected).policy_id == "selected"
    selected.write_bytes(b"invalid=1")
    with pytest.raises(InvalidInput):
        load_policy(selected)


@pytest.mark.parametrize(
    "kind", ["missing", "directory", "symlink", "parent_symlink", "hardlink", "fifo", "oversized"]
)
def test_unsafe_policy_files_are_rejected(tmp_path, kind) -> None:
    target = tmp_path / "selected.toml"
    if kind == "directory":
        target.mkdir()
    elif kind == "symlink":
        target.symlink_to(tmp_path / "real.toml")
    elif kind == "parent_symlink":
        real = tmp_path / "real"
        real.mkdir()
        (real / "selected.toml").write_bytes(default_bytes())
        link = tmp_path / "linked"
        link.symlink_to(real, target_is_directory=True)
        target = link / "selected.toml"
    elif kind == "hardlink":
        real = tmp_path / "real.toml"
        real.write_bytes(default_bytes())
        os.link(real, target)
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "oversized":
        target.write_bytes(b"#" * (MAX_POLICY_BYTES + 1))
    with pytest.raises(InvalidInput):
        load_policy(target)


def test_policy_read_detects_identity_drift(tmp_path, monkeypatch) -> None:
    target = tmp_path / "selected.toml"
    target.write_bytes(default_bytes())
    monkeypatch.setattr(config, "stat_identity", lambda value: object())
    with pytest.raises(InvalidInput, match="changed"):
        load_policy(target)


def test_explicit_optional_mapping_is_supported() -> None:
    data = tomllib.loads(default_bytes().decode())
    data["mandatory_checks"].remove("modelscan")
    data["optional_checks"] = ["modelscan"]
    assert PolicyValidator().parse(render(data)).optional_checks == ("modelscan",)


@pytest.mark.parametrize("machine", [False, True])
def test_policy_validate_cli_is_noninteractive_and_does_not_scan(tmp_path, machine) -> None:
    target = tmp_path / "sensitive name.toml"
    target.write_bytes(default_bytes())
    arguments = [sys.executable, "-m", "modelvet", "policy", "validate", str(target)]
    result = subprocess.run(
        arguments + (["--json"] if machine else []), capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert str(tmp_path) not in result.stdout + result.stderr
    if machine:
        value = json.loads(result.stdout)
        assert value["valid"] is True
        assert value["policy_digest"] == load_policy().semantic_digest
        assert result.stderr == ""
    else:
        assert result.stdout == ""
        assert "Valid policy" in result.stderr


@pytest.mark.parametrize("raw", [None, b"owner='secret-do-not-log'", b"broken = ["])
def test_policy_cli_error_is_40_without_policy_text_or_paths(tmp_path, raw) -> None:
    target = tmp_path / "sensitive-name.toml"
    if raw is not None:
        target.write_bytes(raw)
    result = subprocess.run(
        [sys.executable, "-m", "modelvet", "policy", "validate", str(target), "--json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 40
    assert result.stdout == ""
    assert "exit 40" in result.stderr
    assert "secret-do-not-log" not in result.stderr
    assert str(tmp_path) not in result.stderr


def test_policy_and_decision_schema_snapshots() -> None:
    root = Path(__file__).parents[1] / "schemas"
    for model, name in ((Policy, "policy-v1.json"), (AdmissionDecision, "decision-v1.json")):
        assert model.model_json_schema() == json.loads((root / name).read_text())
