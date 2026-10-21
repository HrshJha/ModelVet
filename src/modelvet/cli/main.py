"""Noninteractive local static assessment CLI."""

import json
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Annotated

import typer
from typer._click.exceptions import UsageError
from typer.exceptions import Abort

from modelvet import __version__
from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.config import load_policy
from modelvet.core.diagnostics import diagnose
from modelvet.core.errors import InvalidInput
from modelvet.core.limits import MIB, ScanLimits
from modelvet.dependencies.advisories import AdvisoryDocument, AdvisoryReader
from modelvet.reports.audit import verify_report
from modelvet.reports.batch import audit_batch
from modelvet.reports.compare import compare_reports
from modelvet.reports.json_report import read_report
from modelvet.reports.privacy import redact


class ExitCode(IntEnum):
    APPROVE = 0
    CONTROLS = 10
    BLOCK = 20
    INSUFFICIENT = 30
    INVALID_INPUT = 40
    INTERNAL_ERROR = 50
    INTERRUPTED = 130


class ScannerChoice(StrEnum):
    AUTO = "auto"
    MODELSCAN = "modelscan"
    NONE = "none"


class ReportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    BOTH = "both"


class InspectFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


_HELP = """Local artifact assessment. Static checks only; model loading not tested.

Exit codes: 0 APPROVE/success; 10 CONTROLS; 20 BLOCK; 30 INSUFFICIENT;
40 invalid input; 50 orchestration error; 130 interrupted.
"""
cli = typer.Typer(
    help=_HELP,
    add_completion=False,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
    invoke_without_command=True,
)
policy_cli = typer.Typer(add_completion=False, no_args_is_help=True)
cli.add_typer(policy_cli, name="policy", help="Validate a local policy.")


@cli.callback()
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@cli.command()
def scan(
    artifact_dir: Annotated[Path, typer.Argument(help="Untrusted local artifact directory.")],
    policy: Annotated[Path | None, typer.Option(help="Local policy TOML.")] = None,
    out: Annotated[Path | None, typer.Option(help="Reports outside artifact directory.")] = None,
    scanner: ScannerChoice = ScannerChoice.AUTO,
    timeout_sec: Annotated[int, typer.Option(min=1)] = 120,
    max_files: Annotated[int, typer.Option(min=1)] = 10000,
    max_file_mib: Annotated[int, typer.Option(min=1)] = 1024,
    max_total_mib: Annotated[int, typer.Option(min=1)] = 2048,
    format: ReportFormat = ReportFormat.BOTH,
    quiet: bool = False,
    json_summary: bool = False,
) -> None:
    """Assess bounded local bytes and write private auditable static reports."""
    limits = ScanLimits(
        max_files=max_files,
        max_file_bytes=max_file_mib * MIB,
        max_total_bytes=max_total_mib * MIB,
        timeout_s=timeout_sec,
    )
    outcome = ScanService().run(
        ScanRequest(artifact_dir, out, policy, scanner.value, limits, format != ReportFormat.JSON)
    )
    states = {"APPROVE": 0, "CONTROLS": 10, "BLOCK": 20, "INSUFFICIENT": 30}
    decision = outcome.report.decision
    summary = {
        "decision": decision.state.value,
        "exit_code": states[decision.state],
        "rule_ids": list(decision.rule_ids),
        "semantic_digest": outcome.report.semantic_digest,
        "report": str(outcome.json_path.relative_to(outcome.output_root)),
        "report_root": "<redacted>",
    }
    if json_summary:
        typer.echo(json.dumps(summary, sort_keys=True))
    if not quiet:
        typer.echo(f"{decision.state.value}: {redact(decision.reason)}", err=True)
        typer.echo(f"Report: <report-root>/{summary['report']}", err=True)
    raise typer.Exit(states[decision.state])


@cli.command()
def inspect(
    report: Annotated[Path, typer.Argument(help="Previously produced JSON report.")],
    format: InspectFormat = InspectFormat.TEXT,
    show_evidence: bool = False,
) -> None:
    """Validate and display a stored report; no fresh assessment or model loading."""
    stored = read_report(report)
    summary = {
        "decision": stored.decision.model_dump(mode="json"),
        "manifest_digest": stored.manifest_digest,
        "semantic_digest": stored.semantic_digest,
        "file_count": len(stored.files),
        "schema_version": stored.schema_version,
        "notice": "Stored report; digest is not a signature or independent attestation.",
    }
    if show_evidence:
        summary["evidence"] = stored.model_dump(mode="json")
    if format == InspectFormat.JSON:
        typer.echo(json.dumps(summary, sort_keys=True))
    else:
        typer.echo(f"Stored decision: {stored.decision.state.value}")
        typer.echo(redact(stored.decision.reason))
        typer.echo(f"Artifact: {stored.manifest_digest}")
        typer.echo(summary["notice"])
        if show_evidence:
            typer.echo(json.dumps(summary["evidence"], sort_keys=True))


@cli.command()
def advisories(
    report: Annotated[Path, typer.Argument(help="Stored report with declared dependency pins.")],
    as_of: Annotated[str, typer.Option(help="Explicit evaluation time, UTC RFC3339.")],
    snapshot: Annotated[
        Path | None, typer.Option(help="Explicit local OSV snapshot envelope.")
    ] = None,
    max_age_days: Annotated[int, typer.Option(min=0, max=365)] = 7,
    required: Annotated[bool, typer.Option("--required/--optional")] = True,
) -> None:
    """Emit offline advisory evidence as JSON; stored admission is not recomputed.

    Exit 30: reported affected version, or unresolved required advisory evidence.
    Exit 0: supplementary check completed under the selected requirement level.
    """
    stored = read_report(report)
    assessment = AdvisoryReader().assess(
        stored.dependencies,
        snapshot_path=snapshot,
        as_of=as_of,
        artifact_digest=stored.manifest_digest,
        report_digest=stored.semantic_digest,
        max_age_days=max_age_days,
        required=required,
    )
    data = AdvisoryDocument.from_assessment(assessment).model_dump(mode="json")
    typer.echo(json.dumps(data, sort_keys=True, ensure_ascii=True))
    raise typer.Exit(assessment.exit_code)


@cli.command()
def verify(
    report: Annotated[Path, typer.Argument(help="Stored report and its declared raw attachments.")],
    expected_report_sha256: Annotated[
        str | None, typer.Option(help="External exact report byte pin.")
    ] = None,
) -> None:
    """Verify stored byte consistency. This does not authenticate or admit a model."""
    audit = verify_report(report, expected_report_sha256=expected_report_sha256)
    typer.echo(audit.model_dump_json())
    raise typer.Exit(0 if audit.status == "VERIFIED" else 30)


@cli.command()
def compare(
    before: Annotated[Path, typer.Argument(help="Earlier stored JSON report.")],
    after: Annotated[Path, typer.Argument(help="Later stored JSON report.")],
    show_paths: bool = False,
    fail_on_change: bool = False,
) -> None:
    """Compare stored assertions without recomputing admission or reading raw files."""
    result = compare_reports(before, after, show_paths=show_paths)
    typer.echo(result.model_dump_json())
    raise typer.Exit(30 if fail_on_change and not result.same_semantics else 0)


@cli.command("audit-batch")
def audit_batch_command(
    manifest: Annotated[Path, typer.Argument(help="Explicit local JSON report list.")],
    root: Annotated[Path, typer.Option(help="Root containing the listed relative report paths.")],
) -> None:
    """Audit a bounded list of stored reports; no model or admission reevaluation."""
    result = audit_batch(manifest, root)
    typer.echo(result.model_dump_json())
    raise typer.Exit(0 if result.status == "VERIFIED" else 30)


@policy_cli.command("validate")
def policy_validate(
    policy: Annotated[Path, typer.Argument(help="Local policy TOML.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate a bounded local TOML policy without scanning any model."""
    selected = load_policy(policy)
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "valid": True,
                    "policy_id": selected.policy_id,
                    "policy_version": selected.policy_version,
                    "policy_digest": selected.semantic_digest,
                },
                sort_keys=True,
            )
        )
    else:
        typer.echo(
            f"Valid policy: {selected.policy_id} v{selected.policy_version} "
            f"({selected.semantic_digest})",
            err=True,
        )


@cli.command()
def doctor(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report capability availability; exit 0 means diagnostics completed."""
    capabilities = diagnose()
    if json_output:
        typer.echo(json.dumps(capabilities, sort_keys=True))
    else:
        for key, value in capabilities.items():
            typer.echo(f"{key}: {json.dumps(value)}", err=True)


@cli.command()
def ui(
    models_root: Annotated[Path, typer.Option(help="Explicit local model-folder root.")],
    workspace: Annotated[
        Path | None, typer.Option(help="Private workspace outside model inputs.")
    ] = None,
    port: Annotated[int, typer.Option(min=0, max=65535)] = 0,
    no_browser: bool = False,
) -> None:
    """Open the optional private local workbench; static assessment only."""
    from modelvet.workbench.launch import launch

    launch(models_root, workspace, port, no_browser)


@cli.command()
def version(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show package version and implemented schema support."""
    if json_output:
        typer.echo(json.dumps({"modelvet_version": __version__, "schema_versions": ["1.0.0"]}))
    else:
        typer.echo(f"ModelVet {__version__} (static report schema 1.0.0)")


def app() -> None:
    """Translate Typer failures to the documented ModelVet exit contract."""
    try:
        result = cli(standalone_mode=False, color=False)
        code = int(result) if isinstance(result, int) else 0
    except UsageError:
        typer.echo("Invalid command or arguments; use modelvet --help (exit 40).", err=True)
        code = ExitCode.INVALID_INPUT
    except InvalidInput as exc:
        typer.echo(f"Invalid input: {exc} (exit 40).", err=True)
        code = ExitCode.INVALID_INPUT
    except (KeyboardInterrupt, Abort):
        typer.echo("Interrupted; no assessment finalized (exit 130).", err=True)
        code = ExitCode.INTERRUPTED
    except Exception:
        typer.echo("Internal orchestration failure; no assessment produced (exit 50).", err=True)
        code = ExitCode.INTERNAL_ERROR
    raise SystemExit(code)
