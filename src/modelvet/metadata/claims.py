"""Read bounded local declarations and preserve their exact source pointers."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from modelvet.core.bytes import read_prefix
from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.classify import Classifier
from modelvet.inventory.identity import ArtifactFile, ArtifactManifest
from modelvet.structural.base import Inspection


@dataclass(frozen=True)
class LocalClaim:
    claim_id: str
    kind: Literal["LICENSE", "PROVENANCE"]
    value: str
    source_ref: str
    source_file_id: str
    source_sha256: str
    source_line: int | None = None
    confidence: str = "DECLARED"


@dataclass(frozen=True)
class MetadataAssessment:
    claims: tuple[LocalClaim, ...]
    checks: dict[str, Inspection]
    missing_kinds: tuple[str, ...]


class UnsupportedClaim(Exception):
    pass


def _claim(
    file: ArtifactFile,
    kind: Literal["LICENSE", "PROVENANCE"],
    value: str,
    pointer: str,
    line: int | None = None,
) -> LocalClaim:
    value = value.strip()
    if not value or len(value) > 4096 or any(ord(char) < 32 for char in value):
        raise UnsupportedClaim("Unsupported declaration text.")
    source = f"{file.file_id}#{pointer}"
    digest = hashlib.sha256(
        json.dumps([kind, value, source], ensure_ascii=False).encode()
    ).hexdigest()
    return LocalClaim(digest, kind, value, source, file.file_id, file.sha256, line)


class MetadataReader:
    def inspect_file(
        self, file: ArtifactFile, snapshot: Snapshot
    ) -> tuple[Inspection, list[LocalClaim]]:
        claims: list[LocalClaim] = []
        limitations = (
            "Local declarations only; source, revision and legal rights are unverified.",
        )
        try:
            if file.size > snapshot.source.limits.max_metadata_bytes:
                raise UnsupportedClaim("Metadata exceeds read ceiling.")
            raw = read_prefix(snapshot, file, file.size)
            path = PurePosixPath(file.relpath)
            if path.suffix.lower() == ".json":
                document = strict_json(raw, snapshot.source.limits.max_metadata_bytes)
                if not isinstance(document, dict):
                    raise InvalidInput("Metadata JSON must be an object.")
                if "license" in document:
                    values = document["license"]
                    values = values if isinstance(values, list) else [values]
                    for index, value in enumerate(values):
                        if not isinstance(value, str):
                            raise UnsupportedClaim("Unsupported license declaration.")
                        pointer = (
                            f"json:/license/{index}"
                            if isinstance(document["license"], list)
                            else "json:/license"
                        )
                        claims.append(_claim(file, "LICENSE", value, pointer))
                for name in ("repo_id", "revision", "_name_or_path", "model_type"):
                    if name in document:
                        value = document[name]
                        if not isinstance(value, str):
                            raise UnsupportedClaim("Unsupported provenance declaration.")
                        claims.append(
                            _claim(file, "PROVENANCE", f"{name}={value}", f"json:/{name}")
                        )
                if "trust_remote_code" in document:
                    flag = document["trust_remote_code"]
                    if type(flag) is not bool:
                        raise UnsupportedClaim("Ambiguous remote-code declaration.")
                    claims.append(
                        _claim(
                            file,
                            "PROVENANCE",
                            f"trust_remote_code={str(flag).lower()}",
                            "json:/trust_remote_code",
                        )
                    )
                if "auto_map" in document:
                    if not isinstance(document["auto_map"], dict):
                        raise UnsupportedClaim("Ambiguous custom-code declaration.")
                    if document["auto_map"]:
                        claims.append(
                            _claim(
                                file,
                                "PROVENANCE",
                                "custom_loader_mapping_declared",
                                "json:/auto_map",
                            )
                        )
            else:
                lines = raw.decode("utf-8", errors="strict").splitlines()
                frontmatter: set[int] = set()
                if lines and lines[0].strip() == "---":
                    end = next(
                        (n for n in range(1, min(len(lines), 201)) if lines[n].strip() == "---"),
                        None,
                    )
                    if end is None:
                        raise UnsupportedClaim("Unterminated or oversized frontmatter.")
                    frontmatter = set(range(1, end))
                for index, line in enumerate(lines):
                    spdx = re.match(
                        r"^\s*(?:[#*;/-]\s*)?SPDX-License-Identifier:\s*(.+?)\s*$", line
                    )
                    if spdx:
                        claims.append(
                            _claim(file, "LICENSE", spdx[1], f"text:L{index + 1}", index + 1)
                        )
                    if index in frontmatter:
                        field = re.match(r"^(license|repo_id|revision):\s*(.*?)\s*$", line)
                        if field:
                            value = field[2]
                            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                                value = value[1:-1]
                            if not re.fullmatch(r"[\w .:/+@-]{1,1024}", value):
                                raise UnsupportedClaim(
                                    "Only simple scalar frontmatter is supported."
                                )
                            kind: Literal["LICENSE", "PROVENANCE"] = (
                                "LICENSE" if field[1] == "license" else "PROVENANCE"
                            )
                            declared = value if kind == "LICENSE" else f"{field[1]}={value}"
                            claims.append(
                                _claim(
                                    file,
                                    kind,
                                    declared,
                                    f"frontmatter:/{field[1]}:L{index + 1}",
                                    index + 1,
                                )
                            )
                if path.name.upper().startswith(("LICENSE", "COPYING")) and not claims:
                    first = next(
                        ((n + 1, line.strip()) for n, line in enumerate(lines) if line.strip()),
                        None,
                    )
                    if first:
                        claims.append(
                            _claim(file, "LICENSE", first[1], f"text-title:L{first[0]}", first[0])
                        )
            result = Inspection("metadata:local", "COMPLETE", limitations=limitations)
        except UnsupportedClaim:
            result = Inspection(
                "metadata:local",
                "UNSUPPORTED",
                "Unsupported or oversized declaration.",
                limitations=limitations,
            )
        except (InvalidInput, UnicodeError):
            result = Inspection(
                "metadata:local",
                "FAILED",
                "Malformed, unreadable or changed metadata.",
                limitations=limitations,
            )
        return result, claims

    def assess(self, snapshot: Snapshot, manifest: ArtifactManifest) -> MetadataAssessment:
        claims: list[LocalClaim] = []
        checks: dict[str, Inspection] = {}
        for file in manifest.files:
            if "metadata:local" in Classifier().classify(file, snapshot).check_ids:
                check, local = self.inspect_file(file, snapshot)
                checks[file.file_id] = check
                claims.extend(local)
        kinds = {claim.kind for claim in claims}
        return MetadataAssessment(
            tuple(claims),
            checks,
            tuple(kind for kind in ("LICENSE", "PROVENANCE") if kind not in kinds),
        )

    def collect_local_claims(
        self, snapshot: Snapshot, manifest: ArtifactManifest
    ) -> list[LocalClaim]:
        return list(self.assess(snapshot, manifest).claims)
