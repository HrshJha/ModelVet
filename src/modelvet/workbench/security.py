"""Loopback capability session and bounded same-origin request boundary."""

import asyncio
import secrets
import threading
import time
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlsplit

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json

COOKIE = "modelvet_session"


class BrowserSession:
    def __init__(self, origin: str, launch_token: str | None = None) -> None:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or not parsed.port
            or parsed.path
        ):
            raise InvalidInput("Workbench origin must be numeric IPv4 loopback with a port.")
        self.origin = origin
        self.host = parsed.netloc
        self.launch_token = launch_token or secrets.token_urlsafe(32)
        self.session_id = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        self.exchanged = False
        self.lock = threading.Lock()

    def authenticated(self, headers: dict[str, str]) -> bool:
        cookie = SimpleCookie()
        try:
            cookie.load(headers.get("cookie", ""))
            value = cookie.get(COOKIE)
            return (
                self.exchanged
                and value is not None
                and secrets.compare_digest(value.value, self.session_id)
            )
        except (CookieError, ValueError, TypeError):
            return False

    def exchange(self, token: str) -> bool:
        with self.lock:
            if self.exchanged or not secrets.compare_digest(
                token.encode(), self.launch_token.encode()
            ):
                return False
            self.exchanged = True
            self.launch_token = ""
            return True


class LocalBoundary:
    def __init__(self, app: ASGIApp, session: BrowserSession) -> None:
        self.app, self.session = app, session
        self.slots = asyncio.Semaphore(4)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/"):
            if self.slots.locked():
                await JSONResponse(
                    {
                        "error": "REQUEST_LIMIT",
                        "message": "Local request capacity is busy. Retry shortly.",
                    },
                    status_code=429,
                    headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
                )(scope, receive, send)
                return
            async with self.slots:
                await self.handle(scope, receive, send)
        else:
            await self.handle(scope, receive, send)

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers: dict[str, str] = {}
        duplicate = False
        for key, value in scope.get("headers", []):
            name = key.decode("latin-1").lower()
            if name in headers and name in {
                "host",
                "origin",
                "content-length",
                "content-type",
                "cookie",
                "x-csrf-token",
            }:
                duplicate = True
            headers[name] = value.decode("latin-1")

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = [
                    *message.get("headers", []),
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (
                        b"content-security-policy",
                        (
                            b"default-src 'self'; script-src 'self'; style-src 'self'; "
                            b"style-src-attr 'unsafe-inline'; img-src 'self' data:; "
                            b"connect-src 'self'; font-src 'self'; object-src 'none'; "
                            b"base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
                        ),
                    ),
                ]
            await send(message)

        async def error(status: int, code: str, message: str) -> None:
            await JSONResponse({"error": code, "message": message}, status_code=status)(
                scope, receive, secured_send
            )

        if duplicate or headers.get("host") != self.session.host:
            await error(403, "HOST_REJECTED", "Open the workbench using its launch address.")
            return
        path, method = scope["path"], scope["method"]
        api = path.startswith("/api/")
        mutation = method not in {"GET", "HEAD"}
        bootstrap = path == "/api/v1/session" and method == "POST"
        if api:
            if "origin" in headers and headers["origin"] != self.session.origin:
                await error(403, "ORIGIN_REJECTED", "Cross-origin requests are not permitted.")
                return
            if not bootstrap and not self.session.authenticated(headers):
                await error(401, "SESSION_REQUIRED", "Launch ModelVet to connect this browser.")
                return
            if mutation:
                if headers.get("origin") != self.session.origin:
                    await error(403, "ORIGIN_REQUIRED", "A same-origin request is required.")
                    return
                if not bootstrap and not secrets.compare_digest(
                    headers.get("x-csrf-token", "").encode("latin-1"), self.session.csrf.encode()
                ):
                    await error(403, "CSRF_REJECTED", "Refresh the workbench and try again.")
                    return
                if headers.get("content-type", "").split(";")[0].strip() != "application/json":
                    await error(415, "JSON_REQUIRED", "Send a JSON request.")
                    return
                limit = 32 * 1024**2 if path == "/api/v1/reports/import" else 64 * 1024
                try:
                    declared = int(headers.get("content-length", "0"))
                    if declared < 0 or declared > limit:
                        raise ValueError
                except ValueError:
                    await error(413, "BODY_LIMIT", "Request exceeds the size limit.")
                    return
                body = bytearray()
                deadline = time.monotonic() + 10
                while True:
                    try:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        chunk = await asyncio.wait_for(receive(), timeout=remaining)
                    except TimeoutError:
                        await error(408, "BODY_TIMEOUT", "Request body did not complete in time.")
                        return
                    if chunk["type"] != "http.request":
                        await error(400, "DISCONNECTED", "Request was interrupted.")
                        return
                    body.extend(chunk.get("body", b""))
                    if len(body) > limit:
                        await error(413, "BODY_LIMIT", "Request exceeds the size limit.")
                        return
                    if not chunk.get("more_body", False):
                        break
                try:
                    strict_json(bytes(body), limit, max_tokens=2_000_000)
                except (InvalidInput, ValueError, RecursionError):
                    await error(400, "INVALID_JSON", "Request is not valid bounded JSON.")
                    return

                async def buffered_receive() -> Message:
                    return {"type": "http.request", "body": bytes(body), "more_body": False}

                await self.app(scope, buffered_receive, secured_send)
                return
        await self.app(scope, receive, secured_send)
