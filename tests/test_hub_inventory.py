"""T-HF-INV-01: immutable revisions, complete bounded inventory, hostile metadata."""

import pytest
from hub_fixtures import COMMIT, FakeHTTPS

from modelvet.hub.client import HubClient
from modelvet.hub.reference import HubReference
from modelvet.hub.transport import HubError


def inventory(client, max_files=10000, revision=None):
    return HubClient(client).inventory(
        HubReference("example/model", revision),
        max_files=max_files,
        max_file_bytes=1024,
        max_total_bytes=2048,
        wall_time_s=600,
    )


def test_pinned_commit_sorted_deterministic_inventory():
    client = FakeHTTPS({"z.json": b"{}", "a.json": b"{}"})
    result = inventory(client)
    assert result.resolved_commit == COMMIT
    assert [f.path for f in result.files] == ["a.json", "z.json"]
    assert all("/tree/" + COMMIT in u for u in client.urls[1:])
    assert result == inventory(FakeHTTPS(client.files))


@pytest.mark.parametrize("path", ["../x", "/x", "a//b", "a/./b", "a\\b", "a\x00b", "a:", "a."])
def test_unsafe_path(path):
    with pytest.raises(HubError):
        inventory(FakeHTTPS(rows=[{"type": "file", "path": path, "size": 1, "oid": COMMIT}]))


@pytest.mark.parametrize(
    "rows",
    [
        [{"type": "symlink", "path": "x", "size": 1, "oid": COMMIT}],
        [{"type": "file", "path": "x", "size": -1, "oid": COMMIT}],
        [{"type": "file", "path": "x", "size": True, "oid": COMMIT}],
        [{"type": "file", "path": "x", "size": 1, "oid": "bad"}],
        [
            {"type": "file", "path": "x", "size": 1, "oid": COMMIT},
            {"type": "file", "path": "X", "size": 1, "oid": COMMIT},
        ],
    ],
)
def test_bad_inventory(rows):
    with pytest.raises(HubError):
        inventory(FakeHTTPS(rows=rows))


def test_pagination_cannot_change_commit_or_loop():
    client = FakeHTTPS({"a": b"x"})
    client.link = (
        '<https://huggingface.co/api/models/example/model/tree/other?cursor=x>; rel="next"'
    )
    with pytest.raises(HubError, match="pagination"):
        inventory(client)


def test_missing_commit_count_cap_and_wrong_commit():
    client = FakeHTTPS({"a": b"x", "b": b"y"})
    with pytest.raises(HubError):
        inventory(client, max_files=1)
    client.info = {}
    with pytest.raises(HubError):
        inventory(client)
    client.info = None
    with pytest.raises(HubError):
        inventory(client, revision="b" * 40)


def test_two_pages_and_directory_rows_are_explicitly_bounded():
    class Pages(FakeHTTPS):
        def response(self, url):
            if "/tree/" in url and "cursor=next" not in url:
                self.rows = [{"type": "directory", "path": "dir", "oid": COMMIT, "size": 0}]
                self.link = (
                    f"<https://huggingface.co/api/models/example/model/tree/{COMMIT}"
                    '?cursor=next>; rel="next"'
                )
            else:
                self.rows = [{"type": "file", "path": "dir/a.json", "oid": COMMIT, "size": 2}]
                self.link = None
            return super().response(url)

    result = inventory(Pages())
    assert [f.path for f in result.files] == ["dir/a.json"]
