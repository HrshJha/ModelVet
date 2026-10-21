"""Inert Hub protocol double. It cannot select a real network endpoint."""

import hashlib
import io
import json
import time
from contextlib import contextmanager

from modelvet.hub.transport import HubError

COMMIT = "a" * 40
URL = "https://huggingface.co/example/model"


def blob(value):
    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()


class Response(io.BytesIO):
    def __init__(self, raw, headers=None):
        super().__init__(raw)
        self.headers = headers or {}
        self.status = 200
        self.fp = None

    def getheader(self, name, default=None):
        return self.headers.get(name, default)


class FakeHTTPS:
    def __init__(self, files=None, *, rows=None):
        self.files = files or {}
        self.rows = rows
        self.urls = []
        self.bodies = []
        self.deadline = time.monotonic() + 600
        self.token = None
        self.commit = COMMIT
        self.info = None
        self.download_headers = {}
        self.downloads = {}
        self.fail = set()
        self.link = None

    @contextmanager
    def response(self, url):
        self.urls.append(url)
        if url in self.fail:
            raise HubError("Controlled fake access failure.")
        if "/api/models/" in url:
            if "/tree/" in url:
                data = (
                    self.rows
                    if self.rows is not None
                    else [
                        {"type": "file", "path": path, "size": len(raw), "oid": blob(raw)}
                        for path, raw in self.files.items()
                    ]
                )
                headers = {"Link": self.link} if self.link else {}
            else:
                data = self.info if self.info is not None else {"sha": self.commit}
                headers = {}
            raw = json.dumps(data).encode()
        else:
            path = url.split("/resolve/" + self.commit + "/", 1)[-1]
            raw = self.downloads.get(path, self.files[path])
            headers = {"Content-Length": str(len(raw)), **self.download_headers}
        response = Response(raw, headers)
        yield response

    def read(self, response, size):
        return response.read(size)
