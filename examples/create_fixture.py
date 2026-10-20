"""Create a new private synthetic directory; never loads or serializes models."""

import argparse
import json
import os
from pathlib import Path


def create(path: Path, variant: str) -> None:
    path.mkdir(mode=0o700)
    header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
    weights = len(header).to_bytes(8, "little") + header + b"\0" * 4
    contents = {
        "weights.safetensors": weights,
        "config.json": json.dumps(
            {
                "license": "MIT",
                "repo_id": "synthetic/modelvet-fixture",
                "revision": "synthetic-fixture-v1",
            }
        ).encode(),
        "README.md": (
            b"Synthetic local fixture, not a trained model. License/provenance fields "
            b"are example declarations; no remote repository or checkpoint is claimed.\n"
        ),
    }
    if variant == "malformed":
        contents["weights.safetensors"] = (999999).to_bytes(8, "little")
    elif variant == "source":
        contents["modeling.py"] = b"# Inert repository source-presence fixture.\n"
    elif variant == "serialized":
        contents["weights.pkl"] = b"\x80\x04N."
    elif variant == "unknown":
        contents["opaque.bin"] = b"\0unknown"
    for name, value in contents.items():
        descriptor = os.open(path / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="New directory; existing paths are refused.")
    parser.add_argument(
        "--variant",
        choices=("clean", "malformed", "source", "serialized", "unknown"),
        default="clean",
    )
    args = parser.parse_args()
    create(args.directory, args.variant)
    print("Created synthetic fixture. No trained model or safety claim.")


if __name__ == "__main__":
    main()
