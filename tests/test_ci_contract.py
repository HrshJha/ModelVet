import re
from pathlib import Path


def test_workflow_has_pinned_actions_least_privilege_and_mac_release_target() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text()
    actions = re.findall(r"uses: ([^\s]+)", workflow)
    assert len(actions) == 3 and all(
        re.fullmatch(r"[\w-]+/[\w-]+@[a-f0-9]{40}", value) for value in actions
    )
    assert "contents: read" in workflow and "persist-credentials: false" in workflow
    assert "pull_request_target" not in workflow and "secrets." not in workflow
    assert "  push:\n    branches: [main]\n  pull_request:" in workflow
    assert "os: [macos-15-intel]" in workflow
    assert "ubuntu-24.04" not in workflow
    assert "timeout-minutes: 35" in workflow
    assert "--require-hashes" in workflow and "--only-binary :all:" in workflow
    assert "uv sync --locked --python 3.12.15" in workflow
    assert "uv run --extra ui mypy src" in workflow and "uv run --extra ui pytest -q" in workflow


def test_release_cache_is_primed_before_offline_tests() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text()
    primer = workflow.index("name: Prime hash-locked runtime cache for offline release tests")
    assert primer < workflow.index("name: Safe unit, property, contract and CLI tests")
    assert "uv export --locked --extra ui --no-dev --no-emit-project" in workflow
    assert (
        '"$RUNNER_TEMP/modelvet-cache-primer/bin/python" --require-hashes --only-binary :all:'
        in workflow
    )
    assert "UV_OFFLINE" not in workflow[:primer]


def test_workbench_ci_builds_and_tests_the_installed_optional_extra() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text()
    for command in (
        'node-version: "24.14.1"',
        "package-manager-cache: false",
        "npm ci --prefix frontend --ignore-scripts",
        "npm run --prefix frontend types",
        "npm run --prefix frontend format:check",
        "npm run --prefix frontend test:browser",
        "playwright install --with-deps chromium",
        "tests/test_workbench_release.py",
        "src/modelvet/workbench/static",
        "tools/workbench_schema.py --check",
    ):
        assert command in workflow
    assert "upload-artifact" not in workflow  # Browser storage state is a private capability.
