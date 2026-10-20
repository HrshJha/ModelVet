"""Local packaging ledger; never imports model artifacts or extracts archives."""

import hashlib
import json
import subprocess
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

root = Path.cwd()
evidence = root / "docs/verification/MV-035"
source_paths = sorted(
    {
        *root.glob("src/modelvet/**/*.py"),
        *root.glob("src/modelvet/**/*.toml"),
        *root.glob("schemas/*.json"),
        *root.glob("tests/**/*.py"),
        *root.glob("docs/*.md"),
        *root.glob("examples/*"),
        *(
            root / name
            for name in (
                "PRD.md",
                "README.md",
                "AGENTS.md",
                "pyproject.toml",
                "uv.lock",
                ".python-version",
            )
        ),
    }
)
source_paths = [p for p in source_paths if p.is_file()]
problems = []
for path in source_paths:
    check = subprocess.run(
        ["git", "diff", "--no-index", "--check", "/dev/null", str(path)],
        capture_output=True,
        text=True,
    )
    # --no-index implies --exit-code: 1 is a content difference, not whitespace failure.
    if check.returncode not in (0, 1) or check.stdout or check.stderr:
        problems.append(
            {
                "path": str(path.relative_to(root)),
                "exit": check.returncode,
                "output": check.stdout + check.stderr,
            }
        )
whitespace = {"reviewed_files": len(source_paths), "problems": problems}
(evidence / "whitespace-review.json").write_text(json.dumps(whitespace, indent=2) + "\n")
assert not problems, problems
wheel = root / "dist/modelvet-0.1.0-py3-none-any.whl"
sdist = root / "dist/modelvet-0.1.0.tar.gz"
with zipfile.ZipFile(wheel) as archive:
    for path in [*root.glob("src/modelvet/**/*.py"), *root.glob("src/modelvet/**/*.toml")]:
        assert archive.read(str(path.relative_to(root / "src"))) == path.read_bytes(), path
    for path in root.glob("schemas/*.json"):
        assert archive.read("modelvet/schemas/" + path.name) == path.read_bytes(), path
    schemas = sorted(
        n for n in archive.namelist() if n.startswith("modelvet/schemas/") and n.endswith(".json")
    )
    assert len(schemas) == 13
with tarfile.open(sdist) as archive:
    prefix = archive.getmembers()[0].name.split("/")[0] + "/"
    names = archive.getnames()
    for path in source_paths:
        item = archive.extractfile(prefix + str(path.relative_to(root)))
        assert item is not None and item.read() == path.read_bytes(), path
    assert not any(
        "/docs/verification/" in n or "/out/" in n or "/benchmarks/results/" in n for n in names
    )
lock_hash = hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest()
assert lock_hash == "a46d68b74ef8036d8bdad809862d3e0fabf77e2f5e078b6f21a5cde8240eeba5"
status = subprocess.run(
    ["git", "status", "--short"], capture_output=True, text=True, check=True
).stdout.splitlines()
head = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()
record = {
    "observed_at": datetime.now(UTC).isoformat(),
    "head_observed": head,
    "worktree_status": status,
    "agent_commits_pushes_tags": False,
    "scope": "PH-12 through PH-14 static report audit extensions; external gates remain pending",
    "artifacts": [
        {
            "path": str(p.relative_to(root)),
            "size": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in (wheel, sdist)
    ],
    "uv_lock_sha256": lock_hash,
    "third_party_dependencies_added": 0,
    "packaged_schemas": schemas,
    "wheel_all_python_sources_and_policy_match": True,
    "sdist_source_tests_docs_schemas_examples_match": True,
    "operational_evidence_excluded": True,
    "source_hashes": {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths
    },
    "full_tests_passed": 558,
    "linux_only_skipped": 1,
    "post_docs_targeted_passed": 103,
    "final_doc_contract_passed": 4,
    "whitespace_review_files": len(source_paths),
    "whitespace_problems": 0,
    "hosted_ci_verified": False,
    "loader_enabled": False,
}
(evidence / "artifacts.json").write_text(json.dumps(record, indent=2) + "\n")
print(
    json.dumps(
        {k: v for k, v in record.items() if k not in ("source_hashes", "worktree_status")}, indent=2
    )
)
