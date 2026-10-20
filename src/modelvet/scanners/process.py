"""POSIX bounded child execution. Resource limits do not provide containment."""

import hashlib
import json
import math
import os
import resource
import selectors
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

PROCESS_LIMITATIONS = (
    ("macOS address-space/data limits unavailable; scanner memory is not OS-bounded.",)
    if sys.platform == "darwin"
    else ()
)


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int
    stdout: bytes
    stderr: bytes
    failure: str | None
    environment_digest: str


def safe_environment(workdir: Path) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(workdir),
        "TMPDIR": str(workdir),
        "LC_ALL": "C",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }


def run_bounded(
    argv: tuple[str, ...], workdir: Path, timeout_s: int, output_limit: int = 1024 * 1024
) -> ProcessResult:
    if not 1 <= timeout_s <= 120 or not 1 <= output_limit <= 1024 * 1024:
        raise ValueError("Process limits outside reviewed bounds.")
    env = safe_environment(workdir)
    fingerprint = hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()

    def limits() -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(timeout_s) + 1,) * 2)
        resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        if sys.platform != "darwin":
            resource.setrlimit(resource.RLIMIT_DATA, (2 * 1024**3,) * 2)
            resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3,) * 2)

    # Executable/version and fixed argv are checked by ModelScanAdapter; no shell.
    with subprocess.Popen(  # noqa: S603 - reviewed adapter boundary; contract tests enforce argv/env.
        argv,
        shell=False,
        cwd=workdir,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
        preexec_fn=limits,
    ) as process:
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        failure = None

        def kill_group() -> None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        try:
            with selectors.DefaultSelector() as selector:
                if process.stdout is None or process.stderr is None:
                    raise RuntimeError("Process pipes missing.")
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                deadline = time.monotonic() + timeout_s
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        failure = "TIMEOUT"
                        kill_group()
                        break
                    for key, _ in selector.select(min(remaining, 0.1)):
                        name = key.data
                        chunk = os.read(key.fd, min(65536, output_limit - len(buffers[name]) + 1))
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        if len(buffers[name]) + len(chunk) > output_limit:
                            buffers[name].extend(chunk[: output_limit - len(buffers[name])])
                            failure = "OUTPUT_LIMIT"
                            kill_group()
                            break
                        buffers[name].extend(chunk)
                    if failure:
                        break
            process.wait(timeout=max(1, deadline - time.monotonic()))
        except BaseException:
            kill_group()
            raise
        finally:
            kill_group()
            process.wait(timeout=5)
        return ProcessResult(
            process.returncode,
            bytes(buffers["stdout"]),
            bytes(buffers["stderr"]),
            failure,
            fingerprint,
        )
