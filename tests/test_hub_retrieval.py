"""T-HF-FETCH/RESOURCE/INTEGRITY-01: bounded, private, atomic complete files only."""

import hashlib
import os

import pytest
from hub_fixtures import COMMIT, FakeHTTPS, blob

from modelvet.hub.reference import HubReference
from modelvet.hub.retrieval import HubLimits, retrieve


def test_exact_files_private_hashes_and_no_partial(tmp_path):
    client = FakeHTTPS({"nested/a.json": b"{}", "README.md": b"hello"})
    stages = []
    source = retrieve(
        HubReference("example/model", None),
        tmp_path,
        HubLimits(),
        client,
        on_progress=stages.append,
    )
    assert source.complete and stages == ["hub_retrieval"]
    for file in source.files:
        path = tmp_path / file.path
        assert file.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
        assert path.stat().st_mode & 0o777 == 0o600
        assert path.stat().st_nlink == 1
    assert not list(tmp_path.rglob(".modelvet-partial*"))
    assert all("/resolve/" + COMMIT in u for u in client.urls[2:])


def test_oversized_and_total_budget_preserve_all_inventory(tmp_path):
    client = FakeHTTPS({"a.json": b"1", "b.json": b"2" * 4, "c.bin": b"3" * 10})
    source = retrieve(
        HubReference("example/model", None),
        tmp_path,
        HubLimits(max_file_bytes=5, max_total_bytes=2),
        client,
    )
    assert [f.status for f in source.files] == ["RETRIEVED", "BUDGET", "OVERSIZED"]
    assert not source.complete
    assert len(client.urls) == 3


@pytest.mark.parametrize(
    "mutation", ["content", "length", "commit", "truncated", "network", "disk"]
)
def test_failed_bytes_never_enter_scan(tmp_path, mutation, monkeypatch):
    client = FakeHTTPS({"a.json": b"{}"})
    if mutation == "content":
        client.downloads["a.json"] = b"[]"
    elif mutation == "length":
        client.download_headers["Content-Length"] = "1000"
    elif mutation == "commit":
        client.download_headers["X-Repo-Commit"] = "b" * 40
    elif mutation == "truncated":
        client.downloads["a.json"] = b"{"
        client.download_headers["Content-Length"] = "2"
    elif mutation == "network":
        client.fail.add(f"https://huggingface.co/example/model/resolve/{COMMIT}/a.json")
    else:

        def fail(*args):
            raise OSError("disk full")

        monkeypatch.setattr(os, "write", fail)
    source = retrieve(HubReference("example/model", None), tmp_path, HubLimits(), client)
    assert source.files[0].status == "FAILED" and source.files[0].sha256 is None
    assert not list(tmp_path.iterdir())


def test_lfs_digest_uses_sha256_not_git_blob(tmp_path):
    raw = b"{}"
    rows = [
        {
            "type": "file",
            "path": "a.json",
            "size": 2,
            "oid": "b" * 40,
            "lfs": {"size": 2, "oid": hashlib.sha256(raw).hexdigest()},
        }
    ]
    source = retrieve(
        HubReference("example/model", None),
        tmp_path,
        HubLimits(),
        FakeHTTPS({"a.json": raw}, rows=rows),
    )
    assert source.complete and source.files[0].blob_id != blob(raw)


def test_cancel_removes_partial(tmp_path):
    client = FakeHTTPS({"a.json": b"{}"})
    original = client.read

    def interrupt(response, size):
        if len(client.urls) > 2:
            raise KeyboardInterrupt
        return original(response, size)

    client.read = interrupt
    with pytest.raises(KeyboardInterrupt):
        retrieve(HubReference("example/model", None), tmp_path, HubLimits(), client)
    assert not list(tmp_path.iterdir())


def test_assessment_deadline_interrupts_and_restores_signal():
    import signal
    import time

    from modelvet.hub.assessment import assessment_deadline
    from modelvet.hub.transport import HubError

    previous = signal.getsignal(signal.SIGALRM)
    with pytest.raises(HubError, match="wall-time"):
        with assessment_deadline(0.02):
            time.sleep(1)
    assert signal.getsignal(signal.SIGALRM) == previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0, 0)


def test_low_free_space_stops_before_any_content_download(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from modelvet.hub import retrieval

    client = FakeHTTPS({"a.json": b"{}"})
    monkeypatch.setattr(retrieval.shutil, "disk_usage", lambda root: SimpleNamespace(free=0))
    result = retrieve(HubReference("example/model", None), tmp_path, HubLimits(), client)
    assert result.files[0].status == "FAILED"
    assert "staging space" in result.files[0].reason
    assert not any("/resolve/" in url for url in client.urls)
    assert not list(tmp_path.iterdir())
