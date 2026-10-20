import { GitCompareArrows, LoaderCircle, Search, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  api,
  importReport,
  navigate,
  type HistoryPage,
  type Summary,
} from "./api";
import { Badge, Empty, Notice, PageHeading, ReportTable } from "./components";

export default function HistoryView({ onChanged }: { onChanged: () => void }) {
  const [page, setPage] = useState<HistoryPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(25);
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const file = useRef<HTMLInputElement>(null);
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
  async function importFile(selected: File | undefined) {
    if (!selected || busy) return;
    setBusy(true);
    setError("");
    try {
      const imported = await importReport(selected);
      onChanged();
      navigate("/reports/" + imported.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const visible =
    page?.items.filter(
      (row) =>
        (!state || row.decision === state) &&
        `${row.label} ${row.decision} ${row.manifest_digest}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    ) || [];
  return (
    <>
      <PageHeading
        eyebrow="PRIVATE LOCAL HISTORY"
        title="An evidence trail worth keeping."
        description="Reports are revalidated against their stored byte pins when listed and opened."
      >
        <button className="secondary" onClick={() => navigate("/compare")}>
          <GitCompareArrows size={14} />
          Compare
        </button>
        <button
          className="primary"
          disabled={busy}
          onClick={() => file.current?.click()}
        >
          {busy ? (
            <LoaderCircle className="spin" size={14} />
          ) : (
            <Upload size={14} />
          )}
          {busy ? "Importing…" : "Import report"}
        </button>
        <input
          hidden
          ref={file}
          type="file"
          accept=".json,application/json"
          aria-label="Choose report JSON"
          onChange={(event) => void importFile(event.target.files?.[0])}
        />
      </PageHeading>
      {error && (
        <Notice error>
          {error} If large reports exceed the aggregate read budget, reduce the
          page size.
        </Notice>
      )}
      <section
        className={"panel history-panel " + (drag ? "drag-active" : "")}
        onDragOver={(event) => {
          event.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDrag(false);
          void importFile(event.dataTransfer.files[0]);
        }}
      >
        <div className="panel-title">
          <div>
            <h2>
              Saved reports{" "}
              {page && <span className="count-tag">{page.total}</span>}
            </h2>
            <p>
              Drop a report JSON here, or import a file. Original bytes are
              preserved.
            </p>
          </div>
        </div>
        <div className="history-toolbar">
          <div className="search-field">
            <Search size={15} />
            <input
              aria-label="Filter this history page"
              placeholder="Filter this page…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <select
            aria-label="Filter visible decisions"
            value={state}
            onChange={(event) => setState(event.target.value)}
          >
            <option value="">All decisions</option>
            {["APPROVE", "CONTROLS", "BLOCK", "INSUFFICIENT"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
          <label>
            Page size
            <select
              aria-label="History page size"
              value={limit}
              onChange={(event) => {
                setLimit(Number(event.target.value));
                setOffset(0);
              }}
            >
              {[1, 10, 25, 50].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
        </div>
        {!page ? (
          !error && (
            <p className="loading-text">
              Reading and validating private history…
            </p>
          )
        ) : visible.length ? (
          <ReportTable reports={visible} />
        ) : (
          <Empty
            title={
              page.total
                ? "No reports match on this page."
                : "No saved assessments yet."
            }
            description={
              page.total
                ? "Clear the visible filters, or move to another page of history."
                : "Create a scan or import an existing ModelVet report to start your history."
            }
          />
        )}
        {page && (
          <div className="pagination">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - limit))}
            >
              Previous
            </button>
            <span>
              {page.total === 0
                ? "0"
                : `${offset + 1}–${Math.min(offset + limit, page.total)}`}{" "}
              of {page.total} reports
            </span>
            <button
              disabled={offset + limit >= page.total}
              onClick={() => setOffset(offset + limit)}
            >
              Next
            </button>
          </div>
        )}
      </section>
      <p className="history-note">
        Report JSON does not include its raw attachment files. Imported
        declarations remain unverified until those bytes are available and
        checked. History stays local until you explicitly remove its workspace.
      </p>
    </>
  );
}

export function DemoGallery() {
  const [reports, setReports] = useState<Summary[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    api<Summary[]>("/demos", undefined, controller.signal)
      .then(setReports)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, []);
  if (error)
    return <Notice error>Demonstration reports are unavailable.</Notice>;
  if (!reports.length) return null;
  const descriptions: Record<string, string> = {
    APPROVE: "All mandatory static predicates complete",
    CONTROLS: "Named deployment conditions apply",
    BLOCK: "Repository source prohibited by policy",
    INSUFFICIENT: "Required evidence remains unresolved",
  };
  return (
    <section className="demo-gallery">
      <div className="demo-gallery-heading">
        <div>
          <span className="eyebrow">EXPLORE BEFORE YOUR FIRST SCAN</span>
          <h2>Four outcomes. No hidden gaps.</h2>
        </div>
        <span className="demo-label">SYNTHETIC DEMONSTRATIONS</span>
      </div>
      <div className="demo-grid">
        {reports.map((report) => (
          <button
            key={report.id}
            onClick={() => navigate("/reports/" + report.id)}
          >
            <Badge state={report.decision} />
            <p>{descriptions[report.decision]}</p>
            <small>
              Open demonstration <span aria-hidden="true">↗</span>
            </small>
          </button>
        ))}
      </div>
      <p className="fine-print">
        Generated inert fixtures, not trained models. Demonstrations are
        separate from your saved scan history.
      </p>
    </section>
  );
}
