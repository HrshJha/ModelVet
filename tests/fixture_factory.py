"""Small inert fixtures created locally; no model object serialization."""

import json
from pathlib import Path


def artifact(root: Path, variant: str = "clean") -> Path:
    root.mkdir()
    header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
    raw = len(header).to_bytes(8, "little") + header + b"\0" * 4
    (root / "weights.safetensors").write_bytes(
        raw if variant != "malformed" else (999999).to_bytes(8, "little")
    )
    (root / "config.json").write_text(
        json.dumps({"license": "MIT", "repo_id": "synthetic/test", "revision": "a" * 40})
    )
    (root / "README.md").write_text("Synthetic non-executable fixture. Not a trained model.\n")
    if variant == "source":
        (root / "modeling.py").write_text("# Inert repository source-presence fixture.\n")
    elif variant == "unknown":
        (root / "opaque.bin").write_bytes(b"\0unknown")
    elif variant == "serialized":
        (root / "weights.pkl").write_bytes(b"\x80\x04N.")
    elif variant == "conflict":
        (root / "README.md").write_text("---\nlicense: Apache-2.0\n---\nSynthetic.\n")
    elif variant == "missing_claim":
        (root / "config.json").write_text("{}")
    return root


def controlled_policy(path: Path) -> Path:
    from importlib.resources import files

    raw = files("modelvet.policies").joinpath("default.toml").read_text()
    raw = raw.replace("controls = []\n", "").replace("control_rules = []\n", "")
    raw += '\n[[controls]]\ncontrol_id = "ISOLATED_LOADING"\nowner = "Fixture deployment owner"\n'
    raw += (
        '\n[[control_rules]]\nrule_id = "ISOLATE-MODEL"\n'
        'condition = "MODEL_PRESENT"\ncontrol_ids = ["ISOLATED_LOADING"]\n'
    )
    path.write_text(raw)
    return path
