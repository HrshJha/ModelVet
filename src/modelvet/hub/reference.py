"""Exact model URL grammar and explicit environment-only credentials."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from modelvet.core.errors import InvalidInput

COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,95}\Z")
REVISION = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,199}\Z")


def validate_revision(value: str) -> str:
    if not REVISION.fullmatch(value) or any(p in {"", ".", ".."} for p in value.split("/")):
        raise InvalidInput("Invalid Hugging Face revision.")
    return value


@dataclass(frozen=True)
class HubReference:
    repo_id: str
    revision: str | None

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repo_id}"

    @classmethod
    def parse(cls, value: str, revision: str | None = None) -> "HubReference":
        message = "Use an HTTPS Hugging Face model URL: https://huggingface.co/owner/model."
        if len(value) > 512 or any(ord(c) < 33 or ord(c) > 126 for c in value):
            raise InvalidInput(message)
        try:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or parsed.netloc.lower() != "huggingface.co"
                or parsed.query
                or parsed.fragment
                or "?" in value
                or "#" in value
                or "%" in value
                or "\\" in value
            ):
                raise ValueError
        except ValueError:
            raise InvalidInput(message) from None
        parts = parsed.path.removesuffix("/").split("/")[1:]
        if len(parts) not in {2, 4} or any(not COMPONENT.fullmatch(p) for p in parts[:2]):
            raise InvalidInput(message)
        if parts[0].lower() in {"datasets", "spaces", "api"} or any(
            ".." in p or "--" in p or p.endswith((".", ".git")) for p in parts[:2]
        ):
            raise InvalidInput(message)
        embedded = None
        if len(parts) == 4:
            if parts[2] != "tree":
                raise InvalidInput(message)
            embedded = validate_revision(parts[3])
        if revision is not None:
            validate_revision(revision)
        if embedded is not None and revision is not None and embedded != revision:
            raise InvalidInput("URL revision and selected revision disagree.")
        return cls("/".join(parts[:2]), revision or embedded)


def selected_token(enabled: bool) -> str | None:
    if not enabled:
        return None
    value = os.environ.get("HF_TOKEN", "")
    if not re.fullmatch(r"hf_[A-Za-z0-9]{8,200}", value):
        raise InvalidInput("HF_TOKEN is missing or invalid; configure a read token locally.")
    return value
