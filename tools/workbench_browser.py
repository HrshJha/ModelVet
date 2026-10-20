"""Test-only loopback fixture server. Never accepts operator artifact paths."""

import json
import os
import sys
import tempfile
from pathlib import Path

import uvicorn

from modelvet.workbench.app import create_app


def main() -> None:
    if os.environ.get("MODELVET_BROWSER_TEST") != "1":
        raise SystemExit("This generated-fixture server is for browser tests only.")
    with tempfile.TemporaryDirectory(prefix="modelvet-browser-") as directory:
        root = Path(directory).resolve()
        models = root / "models"
        models.mkdir()
        for name in (
            "tiny-safetensors",
            "with-repository-code",
            "unknown-content",
            "missing-provenance",
            "serialized-fixture",
        ):
            artifact = models / name
            artifact.mkdir()
            header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
            (artifact / "weights.safetensors").write_bytes(
                len(header).to_bytes(8, "little") + header + b"\0" * 4
            )
            (artifact / "config.json").write_text(
                json.dumps(
                    {"license": "MIT", "repo_id": "synthetic/browser-fixture", "revision": "a" * 40}
                    if name != "missing-provenance"
                    else {}
                )
            )
            if name == "with-repository-code":
                (artifact / "modeling.py").write_text("# Inert source-presence fixture.\n")
            if name == "unknown-content":
                (artifact / "opaque.bin").write_bytes(b"\0unclassified fixture")
            if name == "serialized-fixture":
                (artifact / "weights.pkl").write_bytes(b"\x80\x04N.")
        scanner = root / "trusted-test-tools"
        scanner.mkdir()
        executable = scanner / "modelscan"
        executable.write_text(
            f"#!{sys.executable}\nimport sys,time\n"
            "if '--version' in sys.argv:\n print('modelscan, version 0.8.8');sys.exit(0)\n"
            "time.sleep(30)\nsys.exit(2)\n"
        )
        executable.chmod(0o700)
        os.environ["PATH"] = str(scanner) + ":/usr/bin:/bin"
        origin = "http://127.0.0.1:48231"
        app = create_app(
            models,
            root / "workspace",
            origin,
            launch_token="browser-fixture-launch-token-" + "a" * 32,
        )
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=48231,
            log_level="critical",
            access_log=False,
            proxy_headers=False,
        )


if __name__ == "__main__":
    main()
