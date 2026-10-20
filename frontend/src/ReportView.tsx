import {
  ArrowLeft,
  Check,
  CircleAlert,
  CircleMinus,
  Download,
  FileJson,
  Fingerprint,
  LoaderCircle,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  api,
  dateLabel,
  formatBytes,
  navigate,
  shortDigest,
  type Audit,
  type EvidencePage,
  type Summary,
} from "./api";
import { Badge, CopyButton, Empty, Notice, PageHeading } from "./components";

type Row = Record<string, unknown>;
type Section =
  | "files"
  | "checks"
  | "findings"
  | "claims"
  | "conflicts"
  | "dependencies"
  | "executions"
  | "references";
const tabs: { id: Section; label: string }[] = [
  { id: "files", label: "Files & coverage" },
  { id: "findings", label: "Findings" },
  { id: "claims", label: "Declarations" },
  { id: "conflicts", label: "Conflicts" },
  { id: "dependencies", label: "Dependencies" },
  { id: "executions", label: "Executions" },
  { id: "references", label: "References" },
];
const checkLabels: Record<string, string> = {
  identity: "Identity",
  classification: "Format",
  "structural:safetensors": "Safetensors",
  "structural:zip": "ZIP index",
  "metadata:local": "Metadata",
  "dependencies:declared": "Dependencies",
  "source:presence": "Source code",
  modelscan: "ModelScan",
  "scanner:resources": "Resources",
};
function strings(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}
function field(row: Row, key: string): string {
  return typeof row[key] === "string" ? (row[key] as string) : "";
}
function object(value: unknown): Row {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Row)
    : {};
}
export function checkStatus(coverage: Row, check: string): string {
  if (!strings(coverage.expected_check_ids).includes(check))
    return "NOT_APPLICABLE";
  const states = [
    "completed",
    "failed",
    "unsupported",
    "skipped",
    "inconclusive",
    "not_run",
  ];
  const matches = states.filter((state) =>
    strings(coverage[state + "_check_ids"]).includes(check),
  );
  return matches.length === 1
    ? matches[0].replace("completed", "complete").toUpperCase()
    : "INCONCLUSIVE";
}

function DetailDialog({ row, onClose }: { row: Row; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      className="detail-dialog"
      aria-labelledby="evidence-detail-title"
      onClose={onClose}
    >
      <header>
        <div>
          <p className="eyebrow">VALIDATED REPORT RECORD</p>
          <h2 id="evidence-detail-title">Evidence detail</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Close evidence detail"
          onClick={() => ref.current?.close()}
        >
          <X size={18} />
        </button>
      </header>
      <p className="fine-print">
        Values below are stored evidence and declarations. They are displayed as
        text, not executed.
      </p>
      <pre>{JSON.stringify(row, null, 2)}</pre>
    </dialog>
  );
}

function Files({
  rows,
  onInspect,
}: {
  rows: Row[];
  onInspect: (id: string, name: string) => void;
}) {
  const checks = [
    ...new Set(
      rows.flatMap((row) => strings(object(row.coverage).expected_check_ids)),
    ),
  ];
  return (
    <div className="table-wrap coverage-table">
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Format</th>
            <th>Required</th>
            {checks.map((check) => (
              <th key={check} title={check}>
                {checkLabels[check] || check}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const coverage = object(row.coverage);
            const required = strings(coverage.mandatory_check_ids);
            return (
              <tr key={field(row, "file_id")}>
                <td>
                  <button
                    className="file-drill"
                    onClick={() =>
                      onInspect(field(row, "file_id"), field(row, "relpath"))
                    }
                  >
                    <FileJson size={17} />
                    <span>
                      <strong>{field(row, "relpath")}</strong>
                      <small>
                        {formatBytes(Number(row.size))} ·{" "}
                        {shortDigest(field(row, "sha256"))}
                      </small>
                    </span>
                  </button>
                </td>
                <td>
                  <span className="format-tag">
                    {field(row, "format_class")}
                  </span>
                  {row.mismatch === true && (
                    <small className="mismatch">Signature mismatch</small>
                  )}
                </td>
                <td className="mono">
                  {
                    required.filter(
                      (check) => checkStatus(coverage, check) === "COMPLETE",
                    ).length
                  }
                  <span className="muted"> / {required.length}</span>
                </td>
                {checks.map((check) => {
                  const state = checkStatus(coverage, check);
                  return (
                    <td className="check-cell" key={check}>
                      <span
                        className={"check-state " + state.toLowerCase()}
                        title={`${check} · ${state} · ${required.includes(check) ? "mandatory" : "optional or not applicable"}`}
                        role="img"
                        aria-label={`${check}: ${state}`}
                      >
                        {state === "COMPLETE" ? (
                          <Check size={14} />
                        ) : state === "NOT_APPLICABLE" ? (
                          <CircleMinus size={12} />
                        ) : (
                          <CircleAlert size={14} />
                        )}
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="coverage-legend">
        <span>
          <i className="legend-complete" />
          Complete
        </span>
        <span>
          <i className="legend-unresolved" />
          Unresolved / unsupported
        </span>
        <span>
          <i className="legend-failed" />
          Failed
        </span>
        <span>— Not applicable</span>
        <small>
          Applicable checks for this page. Scroll inside the table to review
          every column.
        </small>
      </div>
    </div>
  );
}

export default function ReportView({ id }: { id: string }) {
  const [report, setReport] = useState<Summary | null>(null);
  const [section, setSection] = useState<Section>("files");
  const [page, setPage] = useState<EvidencePage | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<{ id: string; name: string } | null>(
    null,
  );
  const [detail, setDetail] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [pageError, setPageError] = useState("");
  const [audit, setAudit] = useState<Audit | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [showAllAdvice, setShowAllAdvice] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    api<Summary>(
      "/reports/" + encodeURIComponent(id),
      undefined,
      controller.signal,
    )
      .then(setReport)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [id]);
  useEffect(() => {
    const controller = new AbortController();
    setPage(null);
    setPageError("");
    const timer = setTimeout(
      () => {
        const params = new URLSearchParams({
          offset: String(offset),
          limit: "50",
          q: query,
        });
        if (selected) params.set("file_id", selected.id);
        if (status) params.set("status", status);
        api<EvidencePage>(
          `/reports/${encodeURIComponent(id)}/evidence/${section}?${params}`,
          undefined,
          controller.signal,
        )
          .then(setPage)
          .catch((e) => {
            if (!controller.signal.aborted) setPageError(e.message);
          });
      },
      query ? 250 : 0,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [id, section, query, offset, selected, status]);
  function changeSection(next: Section) {
    setSection(next);
    setOffset(0);
    setQuery("");
    setStatus("");
    setSelected(null);
  }
  async function verify() {
    setVerifying(true);
    setPageError("");
    try {
      setAudit(await api<Audit>(`/reports/${id}/verify`, {}));
    } catch (e) {
      setPageError((e as Error).message);
    } finally {
      setVerifying(false);
    }
  }
  if (error)
    return (
      <Notice error>
        {error} The report is not displayed as a valid assessment.
      </Notice>
    );
  if (!report)
    return (
      <p className="loading-text">
        Validating the report and stored byte identity…
      </p>
    );
  const advice = report.guidance || [];
  return (
    <>
      {report.demo && (
        <div className="demo-banner">
          <ShieldCheck size={17} />
          <strong>DEMONSTRATION REPORT</strong>
          <span>
            Generated inert fixture · not a trained model · excluded from scan
            history
          </span>
        </div>
      )}
      <PageHeading
        eyebrow={
          report.demo ? "SYNTHETIC DEMONSTRATION" : "STORED ARTIFACT ASSESSMENT"
        }
        title={report.label}
        description={`${dateLabel(report.created_at)} · policy ${report.policy_id} v${report.policy_version}`}
      >
        <a
          className="secondary"
          href={`/api/v1/reports/${id}/download`}
          download
        >
          <Download size={14} />
          JSON
        </a>
        <a
          className="secondary"
          href={`/api/v1/reports/${id}/download?format=markdown`}
          download
        >
          <Download size={14} />
          Markdown
        </a>
        {report.model_path && (
          <button
            className="primary"
            onClick={() =>
              navigate("/scan?model=" + encodeURIComponent(report.model_path!))
            }
          >
            <ScanLineIcon />
            New scan
          </button>
        )}
      </PageHeading>
      <section
        className={"panel verdict-panel " + report.decision.toLowerCase()}
      >
        <div className="verdict-heading">
          <div>
            <Badge state={report.decision} />
            <h2>{report.reason}</h2>
            <p>
              Scoped to this artifact and policy. Static assessment does not
              establish universal safety, verified lineage or legal clearance.
            </p>
          </div>
          <span className="verdict-glyph">
            <ShieldCheck size={36} strokeWidth={1.3} />
          </span>
        </div>
        <div className="report-stat-row">
          <div>
            <strong>{report.file_count}</strong>
            <span>files inventoried</span>
          </div>
          <div>
            <strong>
              {report.required_complete}
              <small> / {report.required_total}</small>
            </strong>
            <span>mandatory checks complete</span>
          </div>
          <div>
            <strong>{report.findings_count}</strong>
            <span>findings recorded</span>
          </div>
          <div>
            <strong>{report.conflicts_count}</strong>
            <span>evidence conflicts</span>
          </div>
        </div>
      </section>
      <div className="identity-strip">
        <span>
          <Fingerprint size={15} />
          Artifact
          <CopyButton value={report.manifest_digest} />
        </span>
        <span>
          Policy
          <CopyButton value={report.policy_digest || ""} />
        </span>
        <span>
          Semantic report
          <CopyButton value={report.semantic_digest} />
        </span>
      </div>
      <div className="report-layout">
        <div className="report-main">
          <section className="panel evidence-panel">
            <div
              className="tabs"
              role="tablist"
              aria-label="Report evidence sections"
              onKeyDown={(event) => {
                if (
                  !["ArrowRight", "ArrowLeft", "Home", "End"].includes(
                    event.key,
                  )
                )
                  return;
                event.preventDefault();
                const nodes = Array.from(
                  event.currentTarget.querySelectorAll<HTMLButtonElement>(
                    "[role=tab]",
                  ),
                );
                const current = nodes.indexOf(
                  document.activeElement as HTMLButtonElement,
                );
                const next =
                  event.key === "Home"
                    ? 0
                    : event.key === "End"
                      ? nodes.length - 1
                      : (current +
                          (event.key === "ArrowRight" ? 1 : -1) +
                          nodes.length) %
                        nodes.length;
                nodes[next].click();
                nodes[next].focus();
              }}
            >
              {tabs.map((tab) => (
                <button
                  role="tab"
                  id={"tab-" + tab.id}
                  aria-controls="evidence-content"
                  aria-selected={
                    section === tab.id ||
                    (section === "checks" && tab.id === "files")
                  }
                  tabIndex={
                    section === tab.id ||
                    (section === "checks" && tab.id === "files")
                      ? 0
                      : -1
                  }
                  key={tab.id}
                  onClick={() => changeSection(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <section
              role="tabpanel"
              id="evidence-content"
              aria-labelledby={
                "tab-" + (section === "checks" ? "files" : section)
              }
            >
              {selected && (
                <div className="file-breadcrumb">
                  <button
                    className="text-button"
                    onClick={() => changeSection("files")}
                  >
                    <ArrowLeft size={14} />
                    All files
                  </button>
                  <span className="mono">{selected.name}</span>
                  <span className="count-tag">Check records</span>
                </div>
              )}
              <div className="evidence-toolbar">
                <div className="search-field">
                  <Search size={15} />
                  <input
                    aria-label="Search evidence"
                    maxLength={256}
                    placeholder={
                      section === "files" ? "Search files…" : "Search records…"
                    }
                    value={query}
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setOffset(0);
                    }}
                  />
                </div>
                {(section === "files" || section === "checks") && (
                  <select
                    aria-label="Filter evidence status"
                    value={status}
                    onChange={(event) => {
                      setStatus(event.target.value);
                      setOffset(0);
                    }}
                  >
                    <option value="">All states</option>
                    {section === "files" ? (
                      <>
                        <option value="unresolved">
                          Unresolved required checks
                        </option>
                        <option value="complete">
                          Required checks complete
                        </option>
                      </>
                    ) : (
                      [
                        "COMPLETE",
                        "FAILED",
                        "UNSUPPORTED",
                        "SKIPPED",
                        "INCONCLUSIVE",
                        "NOT_RUN",
                      ].map((value) => <option key={value}>{value}</option>)
                    )}
                  </select>
                )}
                <span>
                  {page
                    ? `${page.total} ${section === "files" ? "files" : "records"}`
                    : "Reading…"}
                </span>
              </div>
              {pageError && <Notice error>{pageError}</Notice>}
              {!page ? (
                !pageError && (
                  <div className="loading-text">
                    <LoaderCircle className="spin" size={15} />
                    Reading validated evidence…
                  </div>
                )
              ) : (
                <>
                  {page.truncated && (
                    <Notice>
                      Some records exceed the preview limit. Download the
                      complete JSON report to inspect them.
                    </Notice>
                  )}
                  {page.items.length === 0 ? (
                    <Empty
                      title={
                        query || status
                          ? "No records match these filters."
                          : `No ${section} recorded.`
                      }
                      description={
                        section === "findings"
                          ? "This is a stored finding count. Review required-check coverage before interpreting it."
                          : section === "claims"
                            ? "Missing declarations remain explicit; ModelVet does not infer legal rights or provenance."
                            : "The report retains its original admission decision."
                      }
                    />
                  ) : section === "files" ? (
                    <Files
                      rows={page.items}
                      onInspect={(file, name) => {
                        setSelected({ id: file, name });
                        setSection("checks");
                        setQuery("");
                        setOffset(0);
                        setStatus("");
                      }}
                    />
                  ) : (
                    <div className="record-list">
                      {page.items.map((row, index) => (
                        <article
                          className="evidence-record"
                          key={String(row.id || row.check_id || index) + index}
                        >
                          <div>
                            <strong className="mono">
                              {field(row, "check_id") ||
                                field(row, "kind") ||
                                field(row, "name") ||
                                field(row, "id") ||
                                `Record ${offset + index + 1}`}
                            </strong>
                            {field(row, "status") && (
                              <Badge state={field(row, "status")} />
                            )}
                            {field(row, "verification_state") && (
                              <span className="format-tag">
                                {field(row, "verification_state")}
                              </span>
                            )}
                          </div>
                          {(field(row, "reason") ||
                            field(row, "description") ||
                            field(row, "value") ||
                            field(row, "pointer") ||
                            field(row, "source_ref")) && (
                            <p>
                              {field(row, "reason") ||
                                field(row, "description") ||
                                field(row, "value") ||
                                field(row, "pointer") ||
                                field(row, "source_ref")}
                            </p>
                          )}
                          <button
                            className="text-button"
                            onClick={() => setDetail(row)}
                          >
                            Inspect record
                            <ArrowRightIcon />
                          </button>
                        </article>
                      ))}
                    </div>
                  )}
                  {page.total > 50 && (
                    <div className="pagination">
                      <button
                        disabled={offset === 0}
                        onClick={() => setOffset(Math.max(0, offset - 50))}
                      >
                        Previous
                      </button>
                      <span>
                        {offset + 1}–{Math.min(offset + 50, page.total)} of{" "}
                        {page.total}
                      </span>
                      <button
                        disabled={offset + 50 >= page.total}
                        onClick={() => setOffset(offset + 50)}
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </section>
          </section>
          <section className="panel provenance-note">
            <h3>What these records mean</h3>
            <p>
              Check status and finding result are different facts. Local
              metadata is a declaration. Scanner findings retain their recorded
              verification state. References identify evidence; a digest is not
              a signature.
            </p>
          </section>
        </div>
        <aside className="report-aside">
          <section className="panel guidance-panel">
            <p className="eyebrow">BASED ON RECORDED EVIDENCE</p>
            <h3>Next steps</h3>
            {advice.length ? (
              <>
                {(showAllAdvice ? advice : advice.slice(0, 3)).map((item) => (
                  <article key={item.id}>
                    <span className="advice-mark">
                      <CircleAlert size={15} />
                    </span>
                    <div>
                      <h4>{item.title}</h4>
                      <p>{item.action}</p>
                      {(item.check_id || item.rule_id) && (
                        <code>{item.check_id || item.rule_id}</code>
                      )}
                    </div>
                  </article>
                ))}
                {advice.length > 3 && (
                  <button
                    className="text-button"
                    onClick={() => setShowAllAdvice(!showAllAdvice)}
                  >
                    {showAllAdvice
                      ? "Show fewer steps"
                      : `Show ${advice.length - 3} more steps`}
                  </button>
                )}
              </>
            ) : (
              <p className="muted">
                All mandatory predicates completed under this recorded policy.
                Review the report scope and limitations before deciding how to
                use the artifact.
              </p>
            )}
            {(report.controls || []).map((control) => (
              <div className="control-owner" key={control.control_id}>
                <strong>{control.control_id}</strong>
                <span>Owner: {control.owner}</span>
              </div>
            ))}
          </section>
          <section className="panel attachment-panel">
            <h3>Check the stored bytes</h3>
            <p>
              Verify declared raw attachments against their recorded hashes.
              This does not authenticate the author or reassess admission.
            </p>
            <button
              className="secondary"
              disabled={verifying || report.demo}
              onClick={() => void verify()}
            >
              {verifying ? (
                <LoaderCircle className="spin" size={14} />
              ) : (
                <Fingerprint size={14} />
              )}
              {verifying ? "Verifying…" : "Verify attachments"}
            </button>
            {report.demo && (
              <p className="fine-print">
                Demonstration data has no live raw attachment workspace.
              </p>
            )}
            {audit && (
              <Notice error={audit.status === "INCOMPLETE"}>
                {audit.status === "VERIFIED"
                  ? "Declared byte checks completed."
                  : "Raw evidence is incomplete."}{" "}
                {audit.verified_attachments} of {audit.declared_attachments}{" "}
                attachments verified.{" "}
                {audit.declared_attachments === 0
                  ? "No scanner raw attachments were declared."
                  : ""}{" "}
                Admission was not recomputed.
              </Notice>
            )}
          </section>
          {(report.limitations || []).length > 0 && (
            <details className="panel limitations">
              <summary>
                Recorded limitations <span>{report.limitations?.length}</span>
              </summary>
              <ul>
                {report.limitations?.map((value) => (
                  <li key={value}>{value}</li>
                ))}
              </ul>
            </details>
          )}
        </aside>
      </div>
      {detail && <DetailDialog row={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

function ScanLineIcon() {
  return <FileJson size={14} />;
}
function ArrowRightIcon() {
  return <span aria-hidden="true">→</span>;
}
