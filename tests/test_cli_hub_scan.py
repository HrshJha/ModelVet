"""T-HF-CLI-01: URL/local routing, auth consent, exits and stored report identity."""

import json

import pytest
from fixture_factory import artifact
from hub_fixtures import URL, FakeHTTPS
from typer.testing import CliRunner

from modelvet.cli.main import cli
from modelvet.hub import assessment


def test_url_scan_uses_existing_exit_contract(tmp_path, monkeypatch):
    root = artifact(tmp_path / "input")
    monkeypatch.setattr(
        assessment,
        "HTTPS",
        lambda **kwargs: FakeHTTPS({p.name: p.read_bytes() for p in root.iterdir()}),
    )
    result = CliRunner().invoke(
        cli,
        [
            "scan",
            URL,
            "--out",
            str(tmp_path / "out"),
            "--scanner",
            "none",
            "--json-summary",
            "--quiet",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["decision"] == "APPROVE"


def test_invalid_url_and_auth_options_do_not_reach_transport(monkeypatch):
    def unexpected(**kwargs):
        pytest.fail("No network request is allowed")

    monkeypatch.setattr(assessment, "HTTPS", unexpected)
    result = CliRunner().invoke(cli, ["scan", "https://evil.example/a/b"])
    assert result.exception is not None
    result = CliRunner().invoke(cli, ["scan", ".", "--revision", "main"])
    assert result.exception is not None
