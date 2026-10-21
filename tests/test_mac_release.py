"""FR-028: Mac scope removes research dependencies without weakening admission."""

import subprocess
import sys
from pathlib import Path

import pytest
from fixture_factory import artifact

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.workbench.guidance import CHECK_ADVICE

ROOT = Path(__file__).parents[1]


def test_mac_scope_is_traceable_and_research_is_deferred() -> None:
    prd = (ROOT / "PRD.md").read_text()
    tasks = (ROOT / "docs/TASKS.md").read_text()
    spec = (ROOT / "docs/MAC_RELEASE_SPEC.md").read_text()
    assert "| FR-028 |" in prd and "MV-045" in prd
    assert "### MV-045" in tasks and "PH-18" in tasks
    assert "DEFERRED" in spec and "do not block" in spec
    assert "independent" in spec.lower() and "not claimed" in spec
    assert "Linux/KVM" in spec and "gate still applies" in spec


def test_published_mac_status_is_consistent_in_project_docs() -> None:
    release = "v0.1.0-mac-preview.1"
    for relative in (
        "PRD.md",
        "docs/ROADMAP.md",
        "docs/TASKS.md",
        "docs/PROGRESS.md",
        "docs/RELEASE_STATUS.md",
        "docs/MAC_RELEASE_SPEC.md",
    ):
        assert release in (ROOT / relative).read_text(), relative
    status = (ROOT / "docs/RELEASE_STATUS.md").read_text()
    assert "independent benchmark" in status.lower()
    assert "Linux/KVM" in status
    assert "published" in status.lower()


def test_mac_resource_guidance_does_not_require_linux_or_manufactured_evidence() -> None:
    title, action = CHECK_ADVICE["scanner:resources"]
    assert "macOS" in action and "unresolved" in action
    assert "Linux" not in title + action
    assert "Do not load unknown files" in action
    assert "publisher" in action


@pytest.mark.parametrize("variant,decision", [("clean", "APPROVE"), ("serialized", "INSUFFICIENT")])
def test_mac_scope_preserves_static_and_missing_scanner_decisions(
    tmp_path, variant, decision
) -> None:
    target = artifact(tmp_path / "input", variant)
    outcome = ScanService().run(ScanRequest(target, tmp_path / "reports", scanner="none"))
    assert outcome.report.decision.state.value == decision
    if variant == "serialized":
        assert any("modelscan" in row.mandatory_unresolved for row in outcome.report.coverage)


@pytest.mark.skipif(sys.platform != "darwin", reason="Actual Darwin resource contract")
def test_mac_memory_limitations_stay_unresolved() -> None:
    from modelvet.scanners.process import PROCESS_LIMITATIONS

    assert PROCESS_LIMITATIONS
    assert any("memory" in value.lower() for value in PROCESS_LIMITATIONS)


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="Source archive has no Git index")
def test_release_tree_excludes_dependency_caches_and_browser_sessions() -> None:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            "frontend/node_modules",
            "frontend/test-results",
            "frontend/playwright-report",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    assert result.stdout == "", "Generated dependencies/browser state must not be tracked"
