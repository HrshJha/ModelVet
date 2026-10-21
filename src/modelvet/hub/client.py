"""Documented REST metadata, commit-pinned tree inventory, no implicit credentials."""

import hashlib
import re
from urllib.parse import quote

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.hub.models import HubFile, HubSource, safe_path
from modelvet.hub.reference import HubReference
from modelvet.hub.transport import HTTPS, HubError


class HubClient:
    def __init__(self, transport: HTTPS) -> None:
        self.transport = transport
        self.digest = hashlib.sha256()
        self.metadata_bytes = 0

    def metadata(self, url: str) -> tuple[object, str | None]:
        with self.transport.response(url) as response:
            raw = bytearray()
            while True:
                chunk = self.transport.read(
                    response, min(65536, 16 * 1024**2 - self.metadata_bytes + 1)
                )
                if not chunk:
                    break
                self.metadata_bytes += len(chunk)
                if self.metadata_bytes > 16 * 1024**2:
                    raise HubError("Hugging Face metadata exceeds the 16 MiB bound.")
                raw.extend(chunk)
            self.digest.update(len(raw).to_bytes(8, "big"))
            self.digest.update(raw)
            link = response.getheader("Link")
        try:
            return strict_json(bytes(raw), 16 * 1024**2, max_tokens=500000), link
        except (ValueError, InvalidInput):
            raise HubError("Hugging Face metadata is malformed.") from None

    def inventory(
        self,
        reference: HubReference,
        *,
        max_files: int,
        max_file_bytes: int,
        max_total_bytes: int,
        wall_time_s: int,
    ) -> HubSource:
        repo = quote(reference.repo_id, safe="/")
        revision = quote(reference.revision, safe="") if reference.revision else None
        info, _ = self.metadata(
            f"https://huggingface.co/api/models/{repo}"
            + (f"/revision/{revision}" if revision else "")
        )
        if (
            not isinstance(info, dict)
            or not isinstance(info.get("sha"), str)
            or not re.fullmatch(r"[a-f0-9]{40}", info["sha"])
        ):
            raise HubError("Hugging Face did not resolve an immutable commit.")
        commit = info["sha"]
        if reference.revision and re.fullmatch(r"[a-f0-9]{40}", reference.revision):
            if reference.revision != commit:
                raise HubError("Hugging Face returned a different commit.")
        base = f"https://huggingface.co/api/models/{repo}/tree/{commit}"
        url: str | None = base + "?recursive=true&expand=false&limit=1000"
        seen_urls: set[str] = set()
        names: set[str] = set()
        files: list[HubFile] = []
        while url:
            if url in seen_urls or len(seen_urls) >= 100 or not url.startswith(base + "?"):
                raise HubError("Hugging Face pagination changed identity or exceeded its bound.")
            seen_urls.add(url)
            page, link = self.metadata(url)
            if not isinstance(page, list):
                raise HubError("Hugging Face repository inventory is malformed.")
            for row in page:
                try:
                    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                        raise ValueError
                    path = safe_path(row["path"])
                    key = path.casefold()
                    if key in names or len(names) >= max_files:
                        raise ValueError
                    names.add(key)
                    if row.get("type") == "directory":
                        continue
                    if (
                        row.get("type") != "file"
                        or type(row.get("size")) is not int
                        or not isinstance(row.get("oid"), str)
                    ):
                        raise ValueError
                    lfs = row.get("lfs")
                    if lfs is not None and (
                        not isinstance(lfs, dict) or lfs.get("size") != row["size"]
                    ):
                        raise ValueError
                    files.append(
                        HubFile(
                            path=path,
                            size=row["size"],
                            blob_id=row["oid"],
                            lfs_sha256=lfs.get("oid") if lfs is not None else None,
                        )
                    )
                except (ValueError, TypeError):
                    raise HubError(
                        "Unsafe, ambiguous or over-budget Hugging Face inventory."
                    ) from None
            url = None
            if link:
                matches = re.findall(r'<([^>]+)>;\s*rel="next"', link)
                if len(matches) > 1 or ("next" in link and not matches):
                    raise HubError("Hugging Face pagination is malformed.")
                url = matches[0] if matches else None
        paths = {f.path.casefold() for f in files}
        if any(
            "/".join(f.path.casefold().split("/")[:i]) in paths
            for f in files
            for i in range(1, len(f.path.split("/")))
        ):
            raise HubError("Repository file and directory paths conflict.")
        return HubSource(
            url=reference.url,
            repo_id=reference.repo_id,
            requested_revision=reference.revision,
            resolved_commit=commit,
            metadata_digest=self.digest.hexdigest(),
            files=tuple(sorted(files, key=lambda f: f.path)),
            max_file_bytes=max_file_bytes,
            max_total_bytes=max_total_bytes,
            wall_time_s=wall_time_s,
        )
