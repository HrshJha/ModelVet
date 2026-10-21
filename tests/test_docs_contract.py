"""Traceability and local links for the implemented static candidate."""

import re
import tomllib
from pathlib import Path
from urllib.parse import unquote

from modelvet import __version__

ROOT = Path(__file__).parents[1]
P0_TESTS = {
    "FR-001": "test_input_gate.py",
    "FR-002": "test_snapshot.py",
    "FR-003": "test_identity.py",
    "FR-004": "test_classify.py",
    "FR-005": "test_structural.py",
    "FR-006": "test_claims.py",
    "FR-007": "test_dependencies.py",
    "FR-008": "test_modelscan_adapter.py",
    "FR-009": "test_evidence.py",
    "FR-010": "test_coverage.py",
    "FR-011": "test_conflicts.py",
    "FR-012": "test_policy.py",
    "FR-013": "test_reports.py",
    "FR-014": "test_cli.py",
    "FR-015": "test_reproducibility.py",
    "FR-016": "test_fail_closed.py",
    "FR-020": "test_doctor.py",
}


def test_p0_requirement_task_test_traceability() -> None:
    prd = (ROOT / "PRD.md").read_text()
    tasks = (ROOT / "docs/TASKS.md").read_text()
    rows = [line for line in prd.splitlines() if re.match(r"\| FR-\d{3} \|", line)]
    p0_ids = {re.search(r"FR-\d{3}", line)[0] for line in rows if "| P0 |" in line}
    assert p0_ids == P0_TESTS.keys()
    for requirement, test in P0_TESTS.items():
        row = next(line for line in rows if requirement in line)
        assert re.search(r"MV-\d{3}", row) and re.search(r"T-[A-Z0-9-]+", row)
        assert (ROOT / "tests" / test).is_file() and requirement in tasks
    ids = re.findall(r"^### (MV-\d{3}) —", tasks, re.M)
    assert ids == [f"MV-{i:03d}" for i in range(1, 54)]


def test_documentation_relative_links_resolve() -> None:
    sources = [
        ROOT / "README.md",
        ROOT / "PRD.md",
        ROOT / "AGENTS.md",
        *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "examples/README.md",
        ROOT / "tools/modelscan/README.md",
    ]
    missing = []
    for source in sources:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source.read_text()):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            path = unquote(target.split("#", 1)[0].strip("<>"))
            if path and not (source.parent / path).exists():
                missing.append((str(source.relative_to(ROOT)), target))
    assert not missing, missing


def test_version_support_and_claim_boundaries_are_explicit() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["version"] == __version__ and project["requires-python"] == ">=3.12,<3.13"
    readme = (ROOT / "README.md").read_text()
    assert "Mac-first" in readme and "independently reviewed" in readme
    assert "Mac-first" in readme and "Windows is unsupported" in readme
    assert "No independently reviewed benchmark or model-loading experiment" in readme
    decisions = (ROOT / "docs/DECISIONS.md").read_text()
    assert len(re.findall(r"\*\*Status:\*\* Proposed", decisions)) == 13
    assert (
        "docs/verification"
        in tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["hatch"]["build"][
            "targets"
        ]["sdist"]["exclude"]
    )


def test_local_audit_extension_requirement_task_test_traceability() -> None:
    prd = (ROOT / "PRD.md").read_text()
    tasks = (ROOT / "docs/TASKS.md").read_text()
    roadmap = (ROOT / "docs/ROADMAP.md").read_text()
    for requirement, task, phase, test in (
        ("FR-022", "MV-033", "PH-12", "test_report_audit.py"),
        ("FR-023", "MV-034", "PH-13", "test_report_compare.py"),
        ("FR-024", "MV-035", "PH-14", "test_report_batch.py"),
    ):
        row = next(line for line in prd.splitlines() if line.startswith(f"| {requirement} |"))
        assert "| P1 |" in row and task in row and "T-" in row
        assert f"### {task} —" in tasks and phase in roadmap
        assert (ROOT / "tests" / test).is_file()
    for schema in (
        "report-audit-v1.json",
        "report-comparison-v1.json",
        "report-batch-manifest-v1.json",
        "report-batch-audit-v1.json",
    ):
        assert (ROOT / "schemas" / schema).is_file()
        assert schema in (ROOT / "docs/REPORT_AUDIT_SPEC.md").read_text()


def test_proposed_hub_requirement_task_test_traceability() -> None:
    prd = (ROOT / "PRD.md").read_text()
    tasks = (ROOT / "docs/TASKS.md").read_text()
    roadmap = (ROOT / "docs/ROADMAP.md").read_text()
    hub_spec = (ROOT / "docs/HUB_ASSESSMENT_SPEC.md").read_text()
    expected = {
        "FR-029": ("MV-046", "T-HF-URL-01"),
        "FR-030": ("MV-047", "T-HF-INV-01"),
        "FR-031": ("MV-048", "T-HF-FETCH-01"),
        "FR-032": ("MV-049", "T-HF-INTEGRITY-01"),
        "FR-033": ("MV-050", "T-HF-COV-01"),
        "FR-034": ("MV-052", "T-HF-E2E-01"),
    }
    for requirement, (task, test_id) in expected.items():
        row = next(line for line in prd.splitlines() if line.startswith(f"| {requirement} |"))
        assert task in row and test_id in row and "P1 next release" in row
        assert f"### {task} —" in tasks and requirement in tasks
        assert (
            "PH-19" in roadmap
            if requirement in {"FR-029", "FR-030", "FR-031", "FR-032"}
            else "PH-20" in roadmap
        )
        assert test_id in hub_spec
    assert "MV-046" in tasks and "first unblocked" in tasks
    assert "implemented in the working tree" in hub_spec
    assert (ROOT / "src/modelvet/hub/assessment.py").is_file()
    assert (
        "Hub URL" in (ROOT / "frontend/src/ScanView.tsx").read_text()
        or "Hugging Face model URL" in (ROOT / "frontend/src/ScanView.tsx").read_text()
    )
