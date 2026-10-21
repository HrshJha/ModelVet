"""Generate frozen, clearly synthetic demonstrations through the real static engine."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from modelvet.application.scan import ScanRequest, ScanService


def generate(output: Path) -> None:
    # Refuse to replace an existing gallery. Builds only package these frozen bytes.
    output.mkdir(mode=0o700)
    manifest = []
    with tempfile.TemporaryDirectory(prefix="modelvet-demo-") as directory:
        parent = Path(directory).resolve()
        for state in ("APPROVE", "CONTROLS", "BLOCK", "INSUFFICIENT"):
            target = parent / state.lower()
            target.mkdir(mode=0o700)
            header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
            (target / "weights.safetensors").write_bytes(
                len(header).to_bytes(8, "little") + header + b"\0" * 4
            )
            (target / "config.json").write_text(
                json.dumps(
                    {
                        "license": "MIT",
                        "repo_id": "synthetic/modelvet-demonstration",
                        "revision": "illustrative-local-bytes-v1",
                    }
                )
            )
            (target / "README.md").write_text(
                "Synthetic demonstration only. Not a trained model, remote checkpoint, "
                "security certification or legal clearance.\n"
            )
            if state == "BLOCK":
                (target / "modeling.py").write_text("# Inert source-presence demonstration.\n")
            if state == "INSUFFICIENT":
                (target / "opaque.bin").write_bytes(b"\0unclassified synthetic bytes")
            policy = None
            if state == "CONTROLS":
                policy = Path(__file__).parents[1] / "examples/controls.toml"
            result = ScanService().run(
                ScanRequest(
                    target,
                    parent / (state.lower() + "-reports"),
                    policy,
                    scanner="none",
                )
            )
            assert result.report.decision.state.value == state
            name = "demo-" + state.lower() + ".json"
            raw = result.json_path.read_bytes()
            (output / name).write_bytes(raw)
            manifest.append(
                {
                    "file": name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "decision": state,
                    "semantic_digest": result.report.semantic_digest,
                }
            )
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "purpose": (
                    "Synthetic static demonstrations. No trained weights or scanner validation."
                ),
                "generator": "tools/workbench_demos.py",
                "reports": manifest,
            },
            indent=2,
        )
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parents[1] / "src/modelvet/workbench/demo"
    )
    generate(parser.parse_args().out)


if __name__ == "__main__":
    main()
