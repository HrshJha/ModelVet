"""Exercise the installed external scanner using only an inert None stream."""

import json
import platform
import tempfile
from pathlib import Path

from modelvet.application.scan import ScanRequest, ScanService


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="modelvet-inert-smoke-") as directory:
        parent = Path(directory).resolve()
        artifact = parent / "artifact"
        artifact.mkdir()
        (artifact / "weights.pkl").write_bytes(b"\x80\x04N.")
        (artifact / "config.json").write_text(
            json.dumps({"license": "MIT", "repo_id": "synthetic/inert", "revision": "a" * 40})
        )
        outcome = ScanService().run(ScanRequest(artifact, parent / "out"))
        checks = [
            c
            for c in outcome.report.checks
            if c.check_id in {"modelscan", "scanner:resources"}
            and c.file_id
            == next(f.file_id for f in outcome.report.files if f.relpath == "weights.pkl")
        ]
        if not any(c.check_id == "modelscan" and c.status == "COMPLETE" for c in checks):
            raise RuntimeError("Installed ModelScan did not establish inert standalone-file proof.")
        expected = "INSUFFICIENT" if platform.system() == "Darwin" else "APPROVE"
        if outcome.report.decision.state != expected:
            raise RuntimeError(
                "Installed scanner/resource contract differs from expected platform behavior."
            )
        print(
            json.dumps(
                {
                    "fixture": "inert None bytes; never deserialized by ModelVet",
                    "platform": platform.system(),
                    "decision": outcome.report.decision.state.value,
                    "checks": [{"id": c.check_id, "status": c.status.value} for c in checks],
                    "tools": [t.model_dump(mode="json") for t in outcome.report.tools],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
