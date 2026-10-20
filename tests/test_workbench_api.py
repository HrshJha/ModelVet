"""FR-025 loopback/session/policy/root boundary acceptance."""

import os
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from workbench_helpers import ORIGIN, TOKEN
from workbench_helpers import ui as ui

from modelvet.core.errors import InvalidInput
from modelvet.workbench.app import create_app
from modelvet.workbench.paths import Workspace


def test_session_required_host_origin_and_token_replay(tmp_path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    app = create_app(root, tmp_path / "work", ORIGIN, launch_token=TOKEN)
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.get("/api/v1/directories").status_code == 401
        assert (
            client.get("/api/v1/directories", headers={"host": "attacker.test:8765"}).status_code
            == 403
        )
        assert client.post("/api/v1/session", json={"token": TOKEN}).status_code == 403
        assert (
            client.post(
                "/api/v1/session", json={"token": "wrong" * 10}, headers={"origin": ORIGIN}
            ).status_code
            == 401
        )
        response = client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
        assert response.status_code == 200
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=strict" in response.headers["set-cookie"]
        assert (
            client.post(
                "/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN}
            ).status_code
            == 401
        )
        assert client.get("/api/v1/session").status_code == 200
        assert (
            client.get("/api/v1/session", headers={"origin": "https://attacker.test"}).status_code
            == 403
        )


def test_csrf_content_type_and_bounded_json(ui) -> None:
    client, _, _, _ = ui
    assert (
        client.post(
            "/api/v1/policies", json={"toml": "invalid"}, headers={"x-csrf-token": "wrong"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/policies", content="x", headers={"content-type": "text/plain"}
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/v1/policies", content=b"x" * 65537, headers={"content-type": "application/json"}
        ).status_code
        == 413
    )
    for body in ('{"toml":"a","toml":"b"}', '{"toml":NaN}', '{"toml":"\\ud800"}', "{"):
        assert (
            client.post(
                "/api/v1/policies", content=body, headers={"content-type": "application/json"}
            ).status_code
            == 400
        )
    assert (
        client.post("/api/v1/policies", json={"toml": "x", "unexpected": "secret"}).status_code
        == 422
    )


def test_directory_browser_rooted_paged_and_links_unselectable(ui) -> None:
    client, root, _, _ = ui
    (root / "a").mkdir()
    (root / "b").mkdir()
    (root / "file.txt").write_text("not served")
    (root / "linked").symlink_to(root / "a", target_is_directory=True)
    page = client.get("/api/v1/directories?limit=1").json()
    assert page["total"] == 3 and len(page["entries"]) == 1
    rows = client.get("/api/v1/directories").json()["entries"]
    assert next(row for row in rows if row["name"] == "linked")["selectable"] is False
    for path in ("../", "/tmp", "linked", "a/../../", "a\\.."):
        assert client.get("/api/v1/directories", params={"path": path}).status_code == 400


def test_policy_import_validates_and_pins_bytes(ui) -> None:
    client, _, workspace, _ = ui
    raw = (Path(__file__).parents[1] / "examples/default.toml").read_text()
    response = client.post("/api/v1/policies", json={"toml": raw})
    assert response.status_code == 200
    key = response.json()["id"]
    assert (workspace / "policies" / f"{key}.toml").read_text() == raw
    assert client.post("/api/v1/policies", json={"toml": raw}).status_code == 200
    (workspace / "policies" / f"{key}.toml").write_text("tampered")
    assert client.post("/api/v1/policies", json={"toml": raw}).status_code == 400
    invalid = client.post("/api/v1/policies", json={"toml": "private_secret = ???"})
    assert invalid.status_code == 400 and "private_secret" not in invalid.text


def test_workspace_lock_permissions_and_overlap(ui, tmp_path) -> None:
    _, root, workspace, _ = ui
    with pytest.raises(InvalidInput, match="owns"):
        Workspace(root, workspace)
    with pytest.raises(InvalidInput):
        Workspace(root, root / "output")
    with pytest.raises(InvalidInput):
        Workspace(root, root.parent)
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o755)
    os.chmod(unsafe, 0o755)
    with pytest.raises(InvalidInput):
        Workspace(root, unsafe)


def test_api_security_headers_and_error_privacy(ui) -> None:
    client, root, _, _ = ui
    response = client.get("/api/v1/directories")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert "script-src 'self'" in response.headers["content-security-policy"]
    error = client.get("/api/v1/directories", params={"path": "../secret"})
    assert str(root.parent) not in error.text and "secret" not in error.text
