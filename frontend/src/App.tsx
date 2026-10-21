import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  CircleAlert,
  Command,
  Cpu,
  FolderOpen,
  GitCompareArrows,
  History,
  LayoutDashboard,
  LoaderCircle,
  Plus,
  Search,
  ShieldCheck,
  ScanLine,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  connect,
  navigate,
  formatBytes,
  type Capabilities,
  type HistoryPage,
  type Job,
  type Summary,
} from "./api";
import {
  Badge,
  Brand,
  Empty,
  Notice,
  PageHeading,
  ReportTable,
} from "./components";
import { ProgressView, ScanSetup } from "./ScanView";
import ReportView from "./ReportView";
import HistoryView, { DemoGallery } from "./HistoryView";
import CompareView from "./CompareView";

const pages = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/scan", label: "New scan", icon: ScanLine },
  { path: "/history", label: "Scan history", icon: History },
  { path: "/compare", label: "Compare", icon: GitCompareArrows },
  { path: "/environment", label: "Environment", icon: Cpu },
];

function useRoute() {
  const read = () =>
    location.hash.startsWith("#/") ? location.hash.slice(1) : "/";
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const update = () => setRoute(read());
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return route;
}

function Overview({
  history,
  capabilities,
  ready,
}: {
  history: HistoryPage;
  capabilities: Capabilities | null;
  ready: boolean;
}) {
  const latest = history.items[0];
  return (
    <>
      <div className="overview-kicker">
        <span className="live-dot" />
        YOUR LOCAL MODEL WORKBENCH
        <span className="version-tag">STATIC · V1</span>
      </div>
      <section className="hero">
        <div>
          <h1>
            Evidence before
            <br />
            <span>execution.</span>
          </h1>
          <p>
            Know what was checked, what wasn’t,
            <br className="desktop-break" /> and why. Every verdict, backed by a
            trail.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={() => navigate("/scan")}>
              <Plus size={16} />
              New scan
              <ArrowRight size={16} />
            </button>
            <span className="hero-note">
              <ShieldCheck size={15} />
              Your files stay local
            </span>
          </div>
        </div>
        <div className="evidence-card">
          <div className="evidence-card-top">
            <span className="mono">THE REVIEW CHAIN</span>
            <span className="tiny-dots">
              <i />
              <i />
              <i />
            </span>
          </div>
          <div className="evidence-artifact">
            <span className="artifact-glyph">
              <ScanLine size={26} />
            </span>
            <div>
              <strong>One artifact. Every required check.</strong>
              <p>Exact bytes · explicit scope</p>
            </div>
          </div>
          <div className="review-chain">
            <div>
              <span>01</span>
              <strong>Identity</strong>
              <small>SHA-256 manifest</small>
            </div>
            <div>
              <span>02</span>
              <strong>Evidence</strong>
              <small>Structure + declarations</small>
            </div>
            <div>
              <span>03</span>
              <strong>Decision</strong>
              <small>Versioned policy</small>
            </div>
          </div>
          <div className="evidence-card-footer">
            <CircleAlert size={13} />
            Unresolved evidence stays unresolved.
          </div>
        </div>
      </section>
      <div className="metrics-grid">
        <div className="metric">
          <span>
            Saved reports
            <History size={15} />
          </span>
          <strong>{ready ? history.total.toLocaleString() : "—"}</strong>
          <small>Private, persistent local history</small>
        </div>
        <div className="metric">
          <span>
            Latest decision
            <Activity size={15} />
          </span>
          <strong className="metric-decision">
            {latest ? <Badge state={latest.decision} /> : "—"}
          </strong>
          <small>
            {latest ? latest.label : "Run a scan to start your evidence trail"}
          </small>
        </div>
        <div className="metric">
          <span>
            Scanner availability
            <Cpu size={15} />
          </span>
          <strong className="scanner-label">
            {capabilities
              ? capabilities.scanner_available
                ? "Available"
                : "Not found"
              : "Checking…"}
          </strong>
          <small>
            {capabilities?.scanner_available
              ? `ModelScan ${capabilities.scanner_version}`
              : "Safetensors checks do not require ModelScan"}
          </small>
        </div>
      </div>
      <section className="panel recent-panel">
        <div className="panel-title">
          <div>
            <h2>Recent assessments</h2>
            <p>Recorded decisions for exact artifact and policy identities.</p>
          </div>
          <button className="text-button" onClick={() => navigate("/history")}>
            All history
            <ArrowUpRight size={15} />
          </button>
        </div>
        {!ready ? (
          <p className="loading-text">Reading private history…</p>
        ) : history.items.length ? (
          <ReportTable reports={history.items.slice(0, 5)} />
        ) : (
          <Empty
            title="Your first evidence trail starts here."
            description="Select a local model folder to create a reproducible static assessment."
          >
            <button className="secondary" onClick={() => navigate("/scan")}>
              Choose a model folder
              <ArrowRight size={15} />
            </button>
          </Empty>
        )}
      </section>
      <DemoGallery />
      <section className="bottom-notes">
        <div>
          <span className="note-icon">
            <ShieldCheck size={19} />
          </span>
          <div>
            <h3>Coverage is evidence, not a safety score.</h3>
            <p>
              Required checks must complete. A no-findings result cannot fill a
              missing assessment.
            </p>
          </div>
        </div>
        <button
          className="text-button"
          onClick={() => navigate("/environment")}
        >
          Check your environment
          <ArrowUpRight size={14} />
        </button>
      </section>
    </>
  );
}

function Environment({ capabilities }: { capabilities: Capabilities | null }) {
  return (
    <>
      <PageHeading
        eyebrow="LOCAL CAPABILITIES"
        title="Know your environment."
        description="Availability is diagnostic information; it is not an admission verdict."
      />
      <section className="panel environment-panel">
        <div className="section-heading">
          <span className="policy-icon">
            <Cpu size={22} />
          </span>
          <div>
            <h2>Runtime and scanner</h2>
            <p>
              Capabilities are captured at launch. Restart the workbench after
              changing installed tools.
            </p>
          </div>
        </div>
        <dl className="environment-list">
          <div>
            <dt>ModelVet</dt>
            <dd>{capabilities?.version || "Checking…"}</dd>
          </div>
          <div>
            <dt>Model root</dt>
            <dd className="mono">{capabilities?.models_root_label || "—"}</dd>
          </div>
          <div>
            <dt>ModelScan</dt>
            <dd>
              {capabilities?.scanner_available
                ? capabilities.scanner_version
                : "Not installed on PATH"}
            </dd>
          </div>
          <div>
            <dt>Serialized scan readiness</dt>
            <dd>
              {capabilities?.serialized_scan_ready
                ? "Required resource capabilities available"
                : "Required capability gaps remain"}
            </dd>
          </div>
          <div>
            <dt>Model execution</dt>
            <dd>Disabled · static review only</dd>
          </div>
          <div>
            <dt>Interface</dt>
            <dd>Authenticated IPv4 loopback</dd>
          </div>
        </dl>
      </section>
      <Notice>
        Mac-first static review: supported safetensors checks do not require
        ModelScan. Serialized files can remain INSUFFICIENT when required
        scanner memory bounds are unavailable. Model execution is disabled.
      </Notice>
      {capabilities?.limitations.map((value) => (
        <Notice key={value}>{value}</Notice>
      ))}
      <section className="panel aside-note">
        <h3>Install the separately pinned scanner</h3>
        <p className="muted">
          Follow the ModelScan setup in the repository’s tools/modelscan guide,
          then launch the workbench with that environment’s executable on PATH.
          Scanner installation is an explicit operator action.
        </p>
        <p className="fine-print">
          The scanner is a host subprocess, not a sandbox. macOS scanner memory
          limits remain unsupported. Required missing capabilities produce
          INSUFFICIENT.
        </p>
      </section>
    </>
  );
}

function JumpDialog({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState("");
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      className="jump-dialog"
      onClose={onClose}
      aria-label="Jump to a page"
    >
      <div className="jump-search">
        <Search size={19} />
        <input
          autoFocus
          aria-label="Find a page"
          placeholder="Where would you like to go?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="icon-button"
          aria-label="Close page search"
          onClick={() => ref.current?.close()}
        >
          <X size={17} />
        </button>
      </div>
      {pages
        .filter((page) =>
          page.label.toLowerCase().includes(query.toLowerCase()),
        )
        .map((page) => (
          <button
            key={page.path}
            onClick={() => {
              navigate(page.path);
              ref.current?.close();
            }}
          >
            <page.icon size={18} />
            {page.label}
            <ArrowRight size={15} />
          </button>
        ))}
      <p className="fine-print">Esc to close · all actions stay local</p>
    </dialog>
  );
}

export default function App() {
  const route = useRoute();
  const [connected, setConnected] = useState(false);
  const [sessionError, setSessionError] = useState("");
  const [error, setError] = useState("");
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [history, setHistory] = useState<HistoryPage>({
    items: [],
    total: 0,
    offset: 0,
    limit: 50,
  });
  const [job, setJob] = useState<Job | null>(null);
  const [jobError, setJobError] = useState("");
  const [jump, setJump] = useState(false);
  const [historyReady, setHistoryReady] = useState(false);
  const routeRef = useRef(route);
  routeRef.current = route;
  const refresh = useCallback(() => {
    setHistoryReady(false);
    api<HistoryPage>("/reports")
      .then((value) => {
        setHistory(value);
        setHistoryReady(true);
        setError("");
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    connect()
      .then(() => {
        setConnected(true);
        api<Capabilities>("/capabilities")
          .then(setCapabilities)
          .catch((e) => setError(e.message));
        api<Job | null>("/scans/active")
          .then(setJob)
          .catch((e) => setError(e.message));
      })
      .catch((e) => setSessionError(e.message));
  }, [refresh]);
  useEffect(() => {
    if (connected && route === "/") refresh();
  }, [connected, route, refresh]);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setJump((value) => !value);
      } else if (
        event.key.toLowerCase() === "n" &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey &&
        !(event.target instanceof HTMLInputElement) &&
        !(event.target instanceof HTMLTextAreaElement) &&
        !(event.target instanceof HTMLSelectElement) &&
        !(event.target as HTMLElement)?.isContentEditable
      ) {
        navigate("/scan");
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);
  useEffect(() => {
    if (!job || !["running", "cancelling"].includes(job.status)) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await api<Job>(
          "/scans/" + job!.id,
          undefined,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setJob(next);
        setJobError("");
        if (!["running", "cancelling"].includes(next.status)) {
          refresh();
          if (next.report_id && routeRef.current.startsWith("/scan/"))
            navigate("/reports/" + next.report_id);
          return;
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        setJobError(
          (e as Error).message || "The local service is not responding.",
        );
      }
      timer = setTimeout(poll, 1000);
    }
    timer = setTimeout(poll, 250);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [job?.id, job?.status, refresh]);

  if (!connected)
    return (
      <main className="connection-page">
        <Brand />
        <div className="panel connect-panel">
          <span className="activity-orb">
            <ShieldCheck size={30} />
          </span>
          <p className="eyebrow">PRIVATE BY DEFAULT</p>
          <h1>
            {sessionError ? "Connect your workbench." : "Connecting locally…"}
          </h1>
          <p>
            Open the private one-use launch link from <code>modelvet ui</code>.
            Your browser session stays on this computer.
          </p>
          {sessionError && <Notice error>{sessionError}</Notice>}
          <button className="secondary" onClick={() => location.reload()}>
            Retry connection
          </button>
        </div>
        <p className="fine-print">
          No accounts. No model uploads. Static artifact review.
        </p>
      </main>
    );
  const shortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘K" : "Ctrl K";
  const path = route.split("?")[0];
  const currentPage = path.startsWith("/reports/")
    ? pages[2]
    : pages.find((page) =>
        page.path === "/" ? path === "/" : path.startsWith(page.path),
      );
  const active = job && ["running", "cancelling"].includes(job.status);
  let content;
  if (path === "/")
    content = (
      <Overview
        history={history}
        capabilities={capabilities}
        ready={historyReady}
      />
    );
  else if (path === "/scan")
    content =
      active && job ? (
        <ProgressView
          job={job}
          connectionError={jobError}
          onCancel={() =>
            void api<Job>(`/scans/${job.id}/cancel`, {})
              .then(setJob)
              .catch((e) => setJobError(e.message))
          }
        />
      ) : (
        <ScanSetup
          capabilities={capabilities}
          initialPath={
            new URLSearchParams(route.split("?")[1] || "").get("model") || ""
          }
          onStarted={(value) => {
            setJob(value);
            navigate("/scan/" + value.id);
          }}
        />
      );
  else if (path.startsWith("/scan/"))
    content =
      job && path.endsWith(job.id) ? (
        <ProgressView
          job={job}
          connectionError={jobError}
          onCancel={() =>
            void api<Job>(`/scans/${job.id}/cancel`, {})
              .then(setJob)
              .catch((e) => setJobError(e.message))
          }
        />
      ) : (
        <Notice>
          Reopen an active scan from the New scan page, or inspect its completed
          report in history.
        </Notice>
      );
  else if (path === "/history") content = <HistoryView onChanged={refresh} />;
  else if (path.startsWith("/reports/"))
    content = <ReportView key={path} id={path.split("/")[2]} />;
  else if (path === "/environment")
    content = <Environment capabilities={capabilities} />;
  else if (path === "/compare") content = <CompareView />;
  else
    content = (
      <Empty
        title="Page not found."
        description="Choose a page from the workspace navigation."
      />
    );
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to main content
      </a>
      <aside className="sidebar">
        <a href="#/" aria-label="ModelVet Workbench overview">
          <Brand />
        </a>
        <div className="nav-section-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {pages.map((page) => (
            <a
              href={"#" + page.path}
              key={page.path}
              aria-label={page.label + (page.path === "/scan" ? " N" : "")}
              aria-current={
                currentPage?.path === page.path ? "page" : undefined
              }
              className={currentPage?.path === page.path ? "active" : ""}
            >
              <page.icon size={18} />
              <span>{page.label}</span>{" "}
              {page.path === "/scan" && <kbd aria-hidden="true">N</kbd>}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-indicator">
            <span className="live-dot" />
            <span>Local session</span>
          </div>
          <p>
            Static checks.
            <br />
            Traceable decisions.
          </p>
          <span className="sidebar-version">
            MODELVET {capabilities?.version || "—"}
          </span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span className="breadcrumb">
            Workbench<span>/</span>
            <strong>
              {path.startsWith("/reports/")
                ? "Report review"
                : currentPage?.label || "Workbench"}
            </strong>
          </span>
          <div className="topbar-actions">
            <button
              className="jump-button"
              aria-label={`Jump to… ${shortcut}`}
              aria-keyshortcuts="Meta+K Control+K"
              onClick={() => setJump(true)}
            >
              <Search size={15} />
              <span>Jump to…</span>
              <kbd aria-hidden="true">{shortcut}</kbd>
            </button>
            <span className="root-label">
              <FolderOpen size={14} />
              {capabilities?.models_root_label}
            </span>
          </div>
        </header>
        {active && job && !path.startsWith("/scan") && (
          <button
            className="active-job-banner"
            onClick={() => navigate("/scan/" + job.id)}
          >
            <LoaderCircle className="spin" size={14} />
            Scan running · {job.label}
            <ArrowRight size={14} />
          </button>
        )}
        <main className="content" id="main-content" tabIndex={-1}>
          {error && <Notice error>{error}</Notice>}
          {content}
        </main>
        <footer className="app-footer">
          <span>
            <ShieldCheck size={13} />
            STATIC ASSESSMENT · LOCAL EVIDENCE
          </span>
          <span>Approval is scoped to the recorded artifact and policy.</span>
        </footer>
      </div>
      {jump && <JumpDialog onClose={() => setJump(false)} />}
    </div>
  );
}
