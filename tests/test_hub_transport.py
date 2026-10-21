"""T-HF-NET-01: fixed hosts, per-hop boundaries, direct pinned sockets, no auth leak."""

import socket
from unittest.mock import Mock

import pytest
from hub_fixtures import Response

from modelvet.hub import transport
from modelvet.hub.transport import HTTPS, HubError, PinnedHTTPS, checked_url, public_addresses


@pytest.mark.parametrize(
    "url",
    [
        "http://huggingface.co/x",
        "https://localhost/x",
        "https://127.0.0.1/x",
        "https://evil.huggingface.co/x",
        "https://huggingface.co:443/x",
        "https://user:token@huggingface.co/x",
        "https://huggingface.co/x#fragment",
        "https://huggingface.co\\@evil/x",
        "https://huggingface.co/x\r\nInjected: true",
    ],
)
def test_endpoint_rejection(url):
    with pytest.raises(HubError):
        checked_url(url)


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "192.168.1.1",
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fc00::1",
        "::ffff:8.8.8.8",
    ],
)
def test_private_or_mapped_dns_rejected(monkeypatch, ip):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, (ip, 443))]
    )
    with pytest.raises(HubError):
        public_addresses("huggingface.co")


def test_mixed_public_private_dns_rejected(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [
            (None, None, None, None, ("8.8.8.8", 443)),
            (None, None, None, None, ("127.0.0.1", 443)),
        ],
    )
    with pytest.raises(HubError):
        public_addresses("huggingface.co")


def test_socket_uses_validated_ip_and_tls_hostname(monkeypatch):
    monkeypatch.setattr(transport, "public_addresses", lambda host: ("8.8.8.8",))
    raw = Mock()
    raw.getpeername.return_value = ("8.8.8.8", 443)
    monkeypatch.setattr(socket, "socket", lambda *args: raw)
    connection = PinnedHTTPS("huggingface.co", timeout=2)
    context = Mock()
    context.wrap_socket.return_value = raw
    connection._context = context
    connection.connect()
    raw.connect.assert_called_once_with(("8.8.8.8", 443))
    context.wrap_socket.assert_called_once_with(raw, server_hostname="huggingface.co")
    connection.close()


def test_cross_origin_redirect_strips_auth_and_never_restores_it(monkeypatch):
    first = Response(b"", {"Location": "https://cdn-lfs-us-1.hf.co/a?signed=private"})
    first.status = 302
    second = Response(b"", {"Location": "https://huggingface.co/final"})
    second.status = 302
    third = Response(b"ok")
    responses = iter([first, second, third])
    requests = []

    class Connection:
        def __init__(self, host, **kwargs):
            self.host = host

        def request(self, method, path, headers):
            requests.append((self.host, headers))

        def getresponse(self):
            return next(responses)

        def close(self):
            pass

    monkeypatch.setattr(transport, "PinnedHTTPS", Connection)
    with HTTPS(token="hf_PRIVATE123").response("https://huggingface.co/start") as response:
        assert response.read() == b"ok"
    assert requests[0][1]["Authorization"] == "Bearer hf_PRIVATE123"
    assert all("Authorization" not in headers for _, headers in requests[1:])


def test_hostile_redirect_never_requests_unapproved_target(monkeypatch):
    response = Response(b"", {"Location": "https://169.254.169.254/latest"})
    response.status = 302
    connection = Mock()
    connection.getresponse.return_value = response
    factory = Mock(return_value=connection)
    monkeypatch.setattr(transport, "PinnedHTTPS", factory)
    with pytest.raises(HubError):
        with HTTPS().response("https://huggingface.co/start"):
            pass
    assert factory.call_count == 1
