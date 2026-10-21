import {
  ArrowRight,
  Check,
  Copy,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CircleX,
  FileJson,
  FolderOpen,
  ShieldCheck,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { dateLabel, navigate, shortDigest, type Summary } from "./api";

export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <ShieldCheck size={23} strokeWidth={1.7} />
      </span>
      <span>
        ModelVet <span className="brand-sub">WORKBENCH</span>
      </span>
    </span>
  );
}

export function Badge({ state }: { state: string }) {
  const Icon = ["APPROVE", "COMPLETE"].includes(state)
    ? CircleCheck
    : ["BLOCK", "FAILED"].includes(state)
      ? CircleX
      : state === "CONTROLS"
        ? ShieldCheck
        : state === "INSUFFICIENT"
          ? CircleAlert
          : CircleHelp;
  return (
    <span className={`badge ${state.toLowerCase()}`}>
      <Icon size={13} />
      {state}
    </span>
  );
}

const decisionScopes: Record<string, string> = {
  APPROVE:
    "Configured static checks completed under this exact policy and artifact identity. This is not proof of malware freedom, loader safety, legal rights or verified provenance.",
  CONTROLS:
    "Static checks completed, but named conditions and owners apply. ModelVet did not test deployment enforcement.",
  BLOCK: "A configured prohibition has independently supported evidence.",
  INSUFFICIENT:
    "Required evidence is missing or unresolved. This is neither an approval nor a finding of malicious behavior.",
};

export function DecisionMark({
  state,
  compact = false,
}: {
  state: string;
  compact?: boolean;
}) {
  const scope = decisionScopes[state];
  return (
    <div className={`decision-mark decision-${state.toLowerCase()}`}>
      <span className="decision-shape" aria-hidden="true">
        {state === "APPROVE"
          ? "✓"
          : state === "BLOCK"
            ? "×"
            : state === "CONTROLS"
              ? "Ⅱ"
              : "–"}
      </span>
      <div>
        <strong>{state}</strong>
        {scope && !compact && <p>{scope}</p>}
      </div>
    </div>
  );
}

const checkGlyphs: Record<string, string> = {
  COMPLETE: "✓",
  SKIPPED: "╱",
  FAILED: "!",
  UNSUPPORTED: "▨",
  INCONCLUSIVE: "?",
  NOT_RUN: "·",
  NOT_APPLICABLE: "—",
};

export function CheckGlyph({
  status,
  required,
}: {
  status: string;
  required: boolean;
}) {
  const label = status === "NOT_APPLICABLE" ? "Not applicable" : status;
  return (
    <span className={`check-glyph check-${status.toLowerCase()}`}>
      <span aria-hidden="true">{checkGlyphs[status] || "?"}</span>
      <span>{label}</span>
      {status !== "NOT_APPLICABLE" && (
        <small aria-label={required ? "Mandatory check" : "Optional check"}>
          {required ? "M" : "O"}
        </small>
      )}
    </span>
  );
}

export function Notice({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={`notice ${error ? "error-notice" : ""}`}
      role={error ? "alert" : "status"}
    >
      <CircleAlert size={17} />
      <span>{children}</span>
    </div>
  );
}

export function Empty({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <FolderOpen size={25} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </div>
  );
}

export function PageHeading({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      {children && <div className="heading-actions">{children}</div>}
    </div>
  );
}

export function ReportTable({ reports }: { reports: Summary[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Artifact</th>
            <th>Decision</th>
            <th>Required checks</th>
            <th>Created</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {reports.map((row) => (
            <tr key={row.id}>
              <td>
                <a className="artifact-link" href={`#/reports/${row.id}`}>
                  <span className="file-icon">
                    <FileJson size={18} />
                  </span>
                  <span>
                    <strong>{row.label}</strong>
                    <small className="mono">
                      {shortDigest(row.manifest_digest)}
                    </small>
                  </span>
                </a>
              </td>
              <td>
                <Badge state={row.decision} />
              </td>
              <td>
                <span className="mono">
                  {row.required_complete}
                  <span className="muted"> / {row.required_total}</span>
                </span>
                <small className="cell-note">complete</small>
              </td>
              <td className="muted nowrap">{dateLabel(row.created_at)}</td>
              <td>
                <button
                  className="icon-button"
                  onClick={() => navigate("/reports/" + row.id)}
                  aria-label={`Open ${row.label}`}
                >
                  <ArrowRight size={17} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(false);
  return (
    <button
      className="text-button mono"
      title={
        error
          ? "Clipboard unavailable; copy from the JSON report"
          : "Copy complete identity"
      }
      onClick={() => {
        void navigator.clipboard
          .writeText(value)
          .then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
          })
          .catch(() => setError(true));
      }}
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? "Copied" : error ? "Clipboard unavailable" : shortDigest(value)}
    </button>
  );
}
