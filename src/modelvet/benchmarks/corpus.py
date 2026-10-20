"""Closed inert recipes and provenance checks, separate from production inspectors."""

import hashlib
import io
import json
import os
import pickletools
import stat
import struct
import zipfile
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.evidence.models import SHA256, ArtifactDigest, WireModel
from modelvet.inventory.discover import FileObservation, stat_identity
from modelvet.inventory.gate import absolute_path, open_directory
from modelvet.inventory.identity import manifest_from_entries

Recipe = Literal[
    "tensor-valid",
    "tensor-truncated",
    "zip-valid",
    "zip-traversal",
    "pickle-none",
    "pickle-int",
    "pickle-truncated",
    "source-present",
    "license-conflict",
    "unknown",
]
RECIPES: tuple[Recipe, ...] = (
    "tensor-valid",
    "tensor-truncated",
    "zip-valid",
    "zip-traversal",
    "pickle-none",
    "pickle-int",
    "pickle-truncated",
    "source-present",
    "license-conflict",
    "unknown",
)
MAX_MANIFEST_BYTES = 1024 * 1024


def fixture_bytes(recipe: Recipe) -> dict[str, bytes]:
    header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
    values = {
        "weights.safetensors": struct.pack("<Q", len(header)) + header + b"\0" * 4,
        "config.json": b'{"license":"MIT","repo_id":"synthetic/benchmark","revision":"v1"}',
    }
    if recipe == "tensor-truncated":
        values["weights.safetensors"] = struct.pack("<Q", 1024)
    elif recipe.startswith("zip-"):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("../outside" if recipe == "zip-traversal" else "archive/data")
            info.date_time = (2020, 1, 1, 0, 0, 0)
            archive.writestr(info, b"inert index fixture; never extracted")
        values = {"weights.zip": output.getvalue(), "config.json": values["config.json"]}
    elif recipe.startswith("pickle-"):
        streams = {
            "pickle-none": b"\x80\x04N.",
            "pickle-int": b"\x80\x04K\x07.",
            "pickle-truncated": b"\x80\x04N",
        }
        values = {"weights.pkl": streams[recipe], "config.json": values["config.json"]}
    elif recipe == "source-present":
        values["modeling.py"] = b"# Inert source-presence marker; no executable body.\n"
    elif recipe == "license-conflict":
        values["README.md"] = b"---\nlicense: Apache-2.0\n---\nSynthetic contradictory claim.\n"
    elif recipe == "unknown":
        values["opaque.bin"] = b"\x00unrecognized-synthetic-format"
    elif recipe != "tensor-valid":
        raise InvalidInput("Unknown benchmark recipe.")
    return values


def fixture_identity(values: dict[str, bytes]) -> str:
    return manifest_from_entries(
        tuple(
            FileObservation(name, len(raw), hashlib.sha256(raw).hexdigest())
            for name, raw in values.items()
        )
    ).manifest_digest


def static_oracle(recipe: Recipe, values: dict[str, bytes]) -> str:
    """Alternative stdlib byte methods; never import production structural parsers."""
    if recipe.startswith("tensor-"):
        raw = values["weights.safetensors"]
        (size,) = struct.unpack("<Q", raw[:8])
        if size > len(raw) - 8:
            return "MALFORMED_STRUCTURE"
        header = json.loads(raw[8 : 8 + size])
        end = header["x"]["data_offsets"][1]
        return "VALID_STRUCTURE" if end == len(raw) - 8 - size == 4 else "MALFORMED_STRUCTURE"
    if recipe.startswith("zip-"):
        with zipfile.ZipFile(io.BytesIO(values["weights.zip"])) as archive:
            names = [item.filename for item in archive.infolist()]
        return (
            "UNSAFE_MEMBER_PATH"
            if any(".." in PurePosixPath(n).parts for n in names)
            else "VALID_STRUCTURE"
        )
    if recipe.startswith("pickle-"):
        try:
            operations = list(pickletools.genops(values["weights.pkl"]))
        except ValueError:
            return "MALFORMED_STRUCTURE"
        if any(op.name not in {"PROTO", "NONE", "BININT1", "STOP"} for op, _, _ in operations):
            raise InvalidInput("Fixture contains an opcode outside the inert allowlist.")
        return "VALID_STRUCTURE"
    if recipe == "source-present" and values["modeling.py"].startswith(b"#"):
        return "SOURCE_PRESENT"
    if recipe == "license-conflict":
        config = json.loads(values["config.json"])
        if config["license"] == "MIT" and b"license: Apache-2.0" in values["README.md"]:
            return "CONFLICTING_CLAIMS"
    if recipe == "unknown" and values["opaque.bin"].startswith(b"\0"):
        return "UNKNOWN_FORMAT"
    raise InvalidInput("Fixture oracle could not establish its development label.")


class FixtureFile(WireModel):
    relpath: str
    sha256: SHA256
    size: Annotated[int, Field(ge=0, le=65536)]


class CorpusCase(WireModel):
    fixture_id: Recipe
    recipe: Recipe
    split: Literal["development"] = "development"
    stratum: Literal["S1", "S2", "S3", "S4"]
    label: Literal[
        "VALID_STRUCTURE",
        "MALFORMED_STRUCTURE",
        "UNSAFE_MEMBER_PATH",
        "SOURCE_PRESENT",
        "CONFLICTING_CLAIMS",
        "UNKNOWN_FORMAT",
    ]
    artifact_digest: ArtifactDigest
    files: Annotated[tuple[FixtureFile, ...], Field(min_length=1, max_length=8)]
    license: Literal["MIT"] = "MIT"
    provenance: Literal["modelvet closed synthetic recipe v1"] = (
        "modelvet closed synthetic recipe v1"
    )
    oracle_method: Literal["stdlib-byte-oracle-v1"] = "stdlib-byte-oracle-v1"
    adjudication: Literal["METHOD_CHECKED_NOT_INDEPENDENT_REVIEW"] = (
        "METHOD_CHECKED_NOT_INDEPENDENT_REVIEW"
    )
    baseline_eligibility: Literal["STANDALONE_PICKLE", "NOT_APPLICABLE"]

    @model_validator(mode="after")
    def verify(self) -> Self:
        values = fixture_bytes(self.recipe)
        files = tuple(
            FixtureFile(relpath=name, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
            for name, raw in sorted(values.items())
        )
        expected_eligibility = (
            "STANDALONE_PICKLE" if self.recipe.startswith("pickle-") else "NOT_APPLICABLE"
        )
        if (
            self.fixture_id != self.recipe
            or files != self.files
            or fixture_identity(values) != self.artifact_digest
            or static_oracle(self.recipe, values) != self.label
            or self.baseline_eligibility != expected_eligibility
        ):
            raise ValueError("Fixture bytes, label, identity or eligibility disagree.")
        return self


class CorpusManifest(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    corpus_id: Literal["modelvet-synthetic-development-v1"]
    generator_sha256: SHA256
    holdout_status: Literal["NOT_SUPPLIED"] = "NOT_SUPPLIED"
    independent_review_status: Literal["PENDING"] = "PENDING"
    cases: Annotated[tuple[CorpusCase, ...], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def unique_cases(self) -> Self:
        if len({c.fixture_id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate benchmark fixture ID.")
        return self


def load_manifest(path: Path) -> CorpusManifest:
    selected = absolute_path(path)
    try:
        parent = open_directory(selected.parent)
        try:
            fd = os.open(selected.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1
                    or before.st_size > MAX_MANIFEST_BYTES
                ):
                    raise InvalidInput("Unsafe or oversized benchmark manifest.")
                raw = stream.read(MAX_MANIFEST_BYTES + 1)
                if (
                    stat_identity(before) != stat_identity(os.fstat(stream.fileno()))
                    or len(raw) != before.st_size
                ):
                    raise InvalidInput("Benchmark manifest changed during read.")
        finally:
            os.close(parent)
    except OSError as exc:
        raise InvalidInput("Cannot safely open benchmark manifest.") from exc
    data = strict_json(raw, MAX_MANIFEST_BYTES)
    try:
        manifest = CorpusManifest.model_validate_json(json.dumps(data))
    except (ValueError, ValidationError) as exc:
        raise InvalidInput("Invalid benchmark manifest or unverifiable fixture.") from exc
    if manifest.generator_sha256 != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise InvalidInput("Benchmark generator changed; freeze and review a new manifest.")
    return manifest


def materialize(case: CorpusCase, directory: Path) -> None:
    """Write only the verified closed recipe to a new owner-only directory."""
    parent = open_directory(absolute_path(directory.parent))
    try:
        os.mkdir(directory.name, 0o700, dir_fd=parent)
        fd = os.open(directory.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for name, raw in fixture_bytes(case.recipe).items():
                target = os.open(
                    name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
                )
                with os.fdopen(target, "wb") as stream:
                    stream.write(raw)
        finally:
            os.close(fd)
    except OSError as exc:
        raise InvalidInput("Cannot exclusively create private benchmark fixture.") from exc
    finally:
        os.close(parent)
