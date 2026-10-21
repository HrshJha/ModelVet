"""Direct HTTPS with exact hosts, pinned public DNS addresses and bounded reads.

No proxy/endpoint environment, automatic redirect, cookies, cache or decompression.
TLS verifies the original hostname while the socket connects to a validated address.
"""

import http.client
import ipaddress
import queue
import socket
import ssl
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urljoin, urlsplit

from modelvet.core.errors import InvalidInput

HOSTS = frozenset(
    {
        "huggingface.co",
        "cdn-lfs.huggingface.co",
        "cdn-lfs-us-1.hf.co",
        "cdn-lfs-eu-1.hf.co",
        "cas-bridge.xethub.hf.co",
        "cas-bridge.xethub-eu.hf.co",
        "us.aws.cdn.hf.co",
        "us.gcp.cdn.hf.co",
        "transfer.xethub.hf.co",
        "transfer.xethub-eu.hf.co",
    }
)


class HubError(InvalidInput):
    """Controlled remote failure; never contains remote response bodies or URLs."""


def public_addresses(host: str) -> tuple[str, ...]:
    answers: queue.Queue[tuple[str, ...] | None] = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            result = tuple(
                dict.fromkeys(
                    str(row[4][0]) for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
                )
            )
        except OSError:
            result = None
        answers.put(result)

    resolver = threading.Thread(target=resolve, daemon=True, name="modelvet-hub-dns")
    resolver.start()
    try:
        addresses = answers.get(timeout=5)
    except queue.Empty:
        raise HubError("Hugging Face DNS resolution timed out.") from None
    resolver.join()
    if addresses is None:
        raise HubError("Hugging Face DNS resolution failed.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or getattr(ip, "is_site_local", False)
            or (isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None)
        ):
            raise HubError("Remote address is outside the permitted public network.")
    if not addresses or len(addresses) > 32:
        raise HubError("Remote DNS response is empty or oversized.")
    return addresses


def checked_url(url: str) -> tuple[str, str]:
    if len(url) > 16384 or any(ord(c) < 33 or ord(c) > 126 for c in url) or "\\" in url:
        raise HubError("Remote redirect rejected.")
    try:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.netloc not in HOSTS
            or parts.fragment
            or parts.username
            or parts.password
            or parts.port is not None
        ):
            raise ValueError
    except ValueError:
        raise HubError("Remote redirect host rejected.") from None
    return parts.netloc, (parts.path or "/") + ("?" + parts.query if parts.query else "")


class PinnedHTTPS(http.client.HTTPSConnection):
    _context: ssl.SSLContext

    def connect(self) -> None:
        timeout = float(self.timeout) if isinstance(self.timeout, (int, float)) else 20.0
        deadline = time.monotonic() + timeout
        addresses = public_addresses(self.host)
        last_error: OSError | None = None
        for address in addresses:
            raw = None
            try:
                # Numeric destination prevents a second, unvalidated DNS lookup.
                family = socket.AF_INET6 if ":" in address else socket.AF_INET
                raw = socket.socket(family, socket.SOCK_STREAM)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise HubError("Hugging Face connection deadline exceeded.")
                raw.settimeout(remaining)
                raw.connect((address, 443))
                raw.settimeout(max(0.001, deadline - time.monotonic()))
                self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
                if ipaddress.ip_address(self.sock.getpeername()[0]) != ipaddress.ip_address(
                    address
                ):
                    self.close()
                    raise HubError("Remote peer identity changed.")
                return
            except OSError as error:
                if raw is not None:
                    raw.close()
                last_error = error
        raise HubError("Hugging Face TLS connection failed.") from last_error


class HTTPS:
    def __init__(self, *, token: str | None = None, wall_time_s: int = 600) -> None:
        self.token = token
        self.deadline = time.monotonic() + wall_time_s

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise HubError("Hugging Face assessment deadline exceeded.")
        return min(20.0, remaining)

    @contextmanager
    def response(self, url: str) -> Iterator[http.client.HTTPResponse]:
        current = url
        authorized = True
        for _ in range(6):
            host, path = checked_url(current)
            connection = PinnedHTTPS(
                host, timeout=self.remaining(), context=ssl.create_default_context()
            )
            yielding = False
            try:
                headers = {
                    "User-Agent": "ModelVet/0.1 (bounded static inspection)",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                }
                if self.token is not None and host == "huggingface.co" and authorized:
                    headers["Authorization"] = "Bearer " + self.token
                connection.request("GET", path, headers=headers)
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise HubError("Hugging Face redirect is incomplete.")
                    target = urljoin(current, location)
                    new_host, _ = checked_url(target)
                    if new_host != host:
                        authorized = False
                    current = target
                    continue
                if response.status != 200:
                    message = (
                        "Repository or revision is inaccessible. For private/gated access, "
                        "configure HF_TOKEN and explicitly enable it."
                        if response.status in {401, 403, 404}
                        else "Hugging Face rate limit reached; retry later."
                        if response.status == 429
                        else "Hugging Face request failed. Retry the assessment later."
                    )
                    raise HubError(message)
                if response.getheader("Content-Encoding", "identity").lower() != "identity":
                    raise HubError("Compressed HTTP transfer is unsupported.")
                yielding = True
                yield response
                return
            except HubError:
                self.deadline = 0
                raise
            except (OSError, http.client.HTTPException, ValueError):
                if yielding:
                    raise
                self.deadline = 0
                raise HubError("Hugging Face transfer failed or timed out.") from None
            finally:
                connection.close()
        raise HubError("Hugging Face redirect limit exceeded.")

    def read(self, response: http.client.HTTPResponse, size: int) -> bytes:
        self.remaining()
        # Tighten the live socket timeout as the assessment deadline approaches.
        if response.fp is not None:
            sock = getattr(getattr(response.fp, "raw", None), "_sock", None)
            if sock is not None:
                sock.settimeout(self.remaining())
        try:
            return response.read1(size)
        except (OSError, http.client.HTTPException):
            self.deadline = 0
            raise HubError("Hugging Face content transfer failed or timed out.") from None
