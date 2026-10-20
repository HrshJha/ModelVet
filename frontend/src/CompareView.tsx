import {
  ArrowLeftRight,
  ArrowRight,
  CircleCheck,
  FileJson,
  GitCompareArrows,
  LoaderCircle,
  Search,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  api,
  dateLabel,
  shortDigest,
  type Comparison,
  type HistoryPage,
  type Summary,
} from "./api";
import { Badge, Empty, Notice, PageHeading } from "./components";

function ReportPicker({
  title,
  onSelect,
  onClose,
}: {
  title: string;
  onSelect: (row: Summary) => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [page, setPage] = useState<HistoryPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(10);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setPage(null);
    setError("");
    api<HistoryPage>(
      `/reports?offset=${offset}&limit=${limit}`,
      undefined,
      controller.signal,
    )
      .then(setPage)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [offset, limit]);
  return (
    <dialog
      ref={dialog}
      className="report-picker"
      aria-labelledby="picker-heading"
      onClose={onClose}
    >
      <header>
        <h2 id="picker-heading">{title}</h2>
        <button
          className="icon-button"
          aria-label="Close report picker"
          onClick={() => dialog.current?.close()}
        >
          <X size={18} />
        </button>
      </header>
      <div className="search-field">
        <Search size={15} />
        <input
          autoFocus
          placeholder="Filter this page…"
          aria-label="Filter report picker page"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      {error && (
        <Notice error>{error} Try page size 1 for large reports.</Notice>
      )}
      {!page ? (
        !error && <p className="loading-text">Validating reports…</p>
      ) : (
        <div className="picker-list">
          {page.items
            .filter((row) =>
              `${row.label} ${row.manifest_digest} ${row.decision}`
                .toLowerCase()
                .includes(query.toLowerCase()),
            )
            .map((row) => (
              <button
                key={row.id}
                onClick={() => {
                  onSelect(row);
                  dialog.current?.close();
                }}
              >
                <span className="file-icon">
                  <FileJson size={18} />
                </span>
                <span>
                  <strong>{row.label}</strong>
                  <small>
                    {dateLabel(row.created_at)} ·{" "}
                    {shortDigest(row.semantic_digest)}
                  </small>
                </span>
                <Badge state={row.decision} />
              </button>
            ))}
          {page.total === 0 && (
            <Empty
              title="No saved reports."
              description="Run a scan or import a report before comparing."
            />
          )}
        </div>
      )}
      <div className="picker-footer">
        <label>
          Page size
          <select
            value={limit}
            aria-label="Picker page size"
            onChange={(event) => {
              setLimit(Number(event.target.value));
              setOffset(0);
            }}
          >
            <option>1</option>
            <option>10</option>
          </select>
        </label>
        <button
          className="text-button"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - limit))}
        >
          Previous
        </button>
        <span>
          {page
            ? `${page.total ? offset + 1 : 0}–${Math.min(offset + limit, page.total)} / ${page.total}`
            : "—"}
        </span>
        <button
          className="text-button"
          disabled={!page || offset + limit >= page.total}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </button>
      </div>
    </dialog>
  );
}

export default function CompareView() {
  const [before, setBefore] = useState<Summary | null>(null);
  const [after, setAfter] = useState<Summary | null>(null);
  const [picker, setPicker] = useState<"before" | "after" | null>(null);
  const [showPaths, setShowPaths] = useState(false);
  const [result, setResult] = useState<Comparison | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function compare() {
    if (!before || !after) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await api<Comparison>("/comparisons", {
          before_id: before.id,
          after_id: after.id,
          show_paths: showPaths,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function selection(side: "before" | "after", row: Summary) {
    if (side === "before") setBefore(row);
    else setAfter(row);
    setResult(null);
  }
  return (
    <>
      <PageHeading
        eyebrow="STORED REPORT COMPARISON"
        title="See what changed."
        description="Compare exact artifact, policy and assessment semantics. Existing admission decisions are displayed as stored."
      />
      <section className="panel compare-setup">
        <div className="comparison-pickers">
          <button className="report-select" onClick={() => setPicker("before")}>
            <span className="eyebrow">BEFORE</span>
            <strong>{before?.label || "Select a baseline report"}</strong>
            <small>
              {before
                ? dateLabel(before.created_at) +
                  " · " +
                  shortDigest(before.manifest_digest)
                : "Choose from private local history"}
            </small>
            {before && <Badge state={before.decision} />}
          </button>
          <span className="comparison-arrow">
            <ArrowRight size={20} />
          </span>
          <button className="report-select" onClick={() => setPicker("after")}>
            <span className="eyebrow">AFTER</span>
            <strong>{after?.label || "Select a report to compare"}</strong>
            <small>
              {after
                ? dateLabel(after.created_at) +
                  " · " +
                  shortDigest(after.manifest_digest)
                : "Choose from private local history"}
            </small>
            {after && <Badge state={after.decision} />}
          </button>
        </div>
        <div className="compare-actions">
          <label>
            <input
              type="checkbox"
              checked={showPaths}
              onChange={(event) => {
                setShowPaths(event.target.checked);
                setResult(null);
              }}
            />
            Show relative filenames in results
          </label>
          <button
            className="primary"
            disabled={!before || !after || busy}
            onClick={() => void compare()}
          >
            {busy ? (
              <LoaderCircle size={15} className="spin" />
            ) : (
              <GitCompareArrows size={15} />
            )}
            {busy ? "Comparing…" : "Compare reports"}
          </button>
        </div>
      </section>
      {error && (
        <Notice error>{error} No comparison result is inferred.</Notice>
      )}
      {!result && !busy && (
        <div className="comparison-intro">
          <ArrowLeftRight size={28} />
          <h3>Changes you can trace.</h3>
          <p>
            Separate artifact changes, policy changes and evidence changes.
            Different reports can still have identical semantics.
          </p>
        </div>
      )}
      {result && (
        <>
          <section
            className={
              "panel comparison-result " + (result.same_semantics ? "same" : "")
            }
          >
            <div className="comparison-result-title">
              <span>
                {result.same_semantics ? (
                  <CircleCheck size={23} />
                ) : (
                  <GitCompareArrows size={23} />
                )}
              </span>
              <div>
                <h2>
                  {result.same_semantics
                    ? "No semantic changes."
                    : "Semantic changes recorded."}
                </h2>
                <p>
                  Stored decisions:{" "}
                  <Badge state={result.stored_decision_before} />
                  <ArrowRight size={13} />
                  <Badge state={result.stored_decision_after} />
                </p>
              </div>
            </div>
            <div className="comparison-metrics">
              <div>
                <span>Artifact identity</span>
                <strong>
                  {result.same_artifact ? "Unchanged" : "Changed"}
                </strong>
              </div>
              <div>
                <span>Policy identity</span>
                <strong>{result.same_policy ? "Unchanged" : "Changed"}</strong>
              </div>
              <div>
                <span>Changed files</span>
                <strong>{result.changed_file_count}</strong>
              </div>
              <div>
                <span>Changed check groups</span>
                <strong>{result.changed_check_count}</strong>
              </div>
            </div>
            {result.changed_sections.length > 0 && (
              <div className="changed-sections">
                <span>Changed sections</span>
                {result.changed_sections.map((value) => (
                  <code key={value}>{value}</code>
                ))}
              </div>
            )}
          </section>
          {(result.omitted_file_changes > 0 ||
            result.omitted_check_changes > 0) && (
            <Notice>
              Preview is bounded: {result.omitted_file_changes} file changes and{" "}
              {result.omitted_check_changes} check changes are omitted. The
              counts include all detected changes.
            </Notice>
          )}
          <section className="panel changes-panel">
            <div className="panel-title">
              <h2>File changes</h2>
              <span className="muted">
                {showPaths
                  ? "Relative paths visible"
                  : "Relative paths suppressed"}
              </span>
            </div>
            {result.files.length ? (
              <div className="table-wrap">
                <table className="change-table">
                  <thead>
                    <tr>
                      <th>File</th>
                      <th>Change</th>
                      <th>Before</th>
                      <th>After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.files.map((row) => (
                      <tr key={row.path_digest}>
                        <td className="mono">
                          {row.relpath ||
                            "file:" + shortDigest(row.path_digest)}
                        </td>
                        <td>
                          <span className="format-tag">{row.kind}</span>
                        </td>
                        <td className="mono muted">
                          {row.before_sha256
                            ? shortDigest(row.before_sha256)
                            : "Not present"}
                        </td>
                        <td className="mono muted">
                          {row.after_sha256
                            ? shortDigest(row.after_sha256)
                            : "Not present"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="loading-text">No file identity changes recorded.</p>
            )}
          </section>
          <section className="panel changes-panel">
            <div className="panel-title">
              <h2>Assessment changes</h2>
            </div>
            {result.checks.length ? (
              <div className="table-wrap">
                <table className="change-table">
                  <thead>
                    <tr>
                      <th>File / check</th>
                      <th>Before states</th>
                      <th>After states</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.checks.map((row) => (
                      <tr key={row.path_digest + row.check_id}>
                        <td>
                          <strong className="mono">{row.check_id}</strong>
                          <small className="cell-note mono">
                            {row.relpath ||
                              "file:" + shortDigest(row.path_digest)}
                          </small>
                        </td>
                        <td className="mono muted">
                          {row.before_statuses.join(", ") || "Not recorded"}
                        </td>
                        <td className="mono muted">
                          {row.after_statuses.join(", ") || "Not recorded"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="loading-text">No check-group changes recorded.</p>
            )}
          </section>
          <Notice>
            {result.notice} Raw attachment declarations are{" "}
            {result.same_declared_raw ? "unchanged" : "different"}; this
            comparison does not verify their bytes.
          </Notice>
        </>
      )}
      {picker && (
        <ReportPicker
          title={
            picker === "before"
              ? "Choose baseline report"
              : "Choose comparison report"
          }
          onClose={() => setPicker(null)}
          onSelect={(row) => selection(picker, row)}
        />
      )}
    </>
  );
}
