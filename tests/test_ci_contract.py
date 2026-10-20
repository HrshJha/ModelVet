import re
from pathlib import Path


def test_workflow_has_pinned_actions_least_privilege_and_both_platform_targets() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text()
    actions = re.findall(r"uses: ([^\s]+)", workflow)
    assert len(actions) == 2 and all(
        re.fullmatch(r"[\w-]+/[\w-]+@[a-f0-9]{40}", value) for value in actions
    )
    assert "contents: read" in workflow and "persist-credentials: false" in workflow
    assert "pull_request_target" not in workflow and "secrets." not in workflow
    assert "ubuntu-24.04" in workflow and "macos-15" in workflow
    assert "timeout-minutes: 25" in workflow
    assert "--require-hashes" in workflow and "--only-binary :all:" in workflow
    assert "uv sync --locked --python 3.12.15" in workflow
    assert "uv run mypy src" in workflow and "uv run pytest -q" in workflow
