"""Conservative best-effort redaction of free text, never file identities."""

import re

SENSITIVE_FIELD_PATTERN = (
    r"(?:access[_-]?token|refresh[_-]?token|client[_-]?secret|token|password|"
    r"secret|api[_-]?key|authorization)"
)


def redact(value: str, roots: tuple[str, ...] = ()) -> str:
    for root in sorted(set(roots), key=len, reverse=True):
        if root and root != "/":
            value = value.replace(root, "<host-path>")
    value = re.sub(r"(?i)(https?://)[^\s/@:]+:[^\s/@]+@", r"\1<credentials>@", value)
    value = re.sub(
        rf"""(?is)(\b{SENSITIVE_FIELD_PATTERN}["']?\s*[:=]\s*)(["'])(.*?)\2""",
        r"\1\2<redacted>\2",
        value,
    )
    value = re.sub(
        r"""(?i)(\bauthorization["']?\s*[:=]\s*["']?)(?:(?:Bearer|Basic)\s+)?[^\s&;,"']+""",
        r"\1<redacted>",
        value,
    )
    value = re.sub(
        rf"""(?i)(\b{SENSITIVE_FIELD_PATTERN}["']?\s*[:=]\s*)[^\s&;,"']+""",
        r"\1<redacted>",
        value,
    )
    value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer <redacted>", value)
    value = re.sub(
        r"\b(?:(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]{8,}|sk-[A-Za-z0-9_-]{8,})\b",
        "<redacted>",
        value,
    )
    value = re.sub(
        r"(?<![\w:])/(?:Users|home|private|tmp|var|etc|opt)/[^\s\"'<>`]*", "<host-path>", value
    )
    return "".join(c if ord(c) >= 32 and ord(c) != 127 else " " for c in value)
