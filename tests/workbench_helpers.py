"""Inert fixtures and a real authenticated local API client."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from modelvet.workbench.app import create_app

ORIGIN = "http://127.0.0.1:8765"
TOKEN = "fixture-launch-capability-" + "a" * 32


@pytest.fixture
def ui(tmp_path):
    root = tmp_path / "models"
    root.mkdir()
    workspace = tmp_path / "workspace"
    app = create_app(root, workspace, ORIGIN, launch_token=TOKEN)
    with TestClient(app, base_url=ORIGIN) as client:
        login = client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
        assert login.status_code == 200
        client.headers.update({"origin": ORIGIN, "x-csrf-token": login.json()["csrf_token"]})
        yield client, root, workspace, app
