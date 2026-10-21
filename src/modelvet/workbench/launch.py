"""Launch a single-user loopback server with an ephemeral browser capability."""

import os
import socket
import webbrowser
from pathlib import Path

from modelvet.core.errors import InvalidInput


def launch(models_root: Path, workspace: Path | None, port: int, no_browser: bool) -> None:
    try:
        import uvicorn

        from modelvet.workbench.app import create_app
    except ImportError as exc:
        raise InvalidInput(
            "Install the optional UI dependencies with uv sync --extra ui --locked."
        ) from exc
    previous_umask = os.umask(0o077)
    app = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))
            listener.listen(128)
            selected_port = listener.getsockname()[1]
            origin = f"http://127.0.0.1:{selected_port}"
            app = create_app(
                models_root, workspace or Path.home() / ".local/state/modelvet/workbench", origin
            )
            url = origin + "/#launch=" + app.state.browser_session.launch_token
            print(f"ModelVet Workbench: {origin} (local only)", flush=True)
            if no_browser or not webbrowser.open(url):
                # Explicit private handoff to the local operator; never an HTTP access log.
                print(f"Private one-use launch link: {url}", flush=True)
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=selected_port,
                log_level="critical",
                access_log=False,
                proxy_headers=False,
                server_header=False,
                timeout_keep_alive=5,
                limit_concurrency=32,
                limit_max_requests=None,
            )
            uvicorn.Server(config).run(sockets=[listener])
    finally:
        if app is not None:
            app.state.workspace.close()
        os.umask(previous_umask)
