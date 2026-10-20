import type { components } from './generated-api';

export type Summary = components['schemas']['ReportSummary'];
export type Job = components['schemas']['JobRecord'];
export type Capabilities = components['schemas']['Capabilities'];
export type DirectoryPage = components['schemas']['DirectoryPage'];
export type Policy = components['schemas']['PolicyResponse'];
export type ScanInput = components['schemas']['ScanInput'];
export type HistoryPage = components['schemas']['ReportPage'];
export type EvidencePage = components['schemas']['EvidencePage'];
export type Audit = components['schemas']['ReportAudit'];
export type Comparison = components['schemas']['ReportComparison'];

export async function importReport(file: File): Promise<Summary> {
  if (file.size > 32 * 1024 ** 2) throw new Error('Reports must be no larger than 32 MiB.');
  const response = await fetch('/api/v1/reports/import', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
    body: await file.arrayBuffer(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'The report could not be imported.');
  }
  return response.json();
}

let csrf = '';

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch('/api/v1' + path, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', signal,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.message || error.detail || 'The local request could not be completed.');
  }
  return response.json() as Promise<T>;
}

export async function connect(): Promise<void> {
  const fragment = new URLSearchParams(location.hash.slice(1));
  const token = fragment.get('launch');
  if (token) history.replaceState(null, '', location.pathname + '#/');
  const session = await api<{ csrf_token: string }>('/session', token ? { token } : undefined);
  csrf = session.csrf_token;
}

export function navigate(path: string) { location.hash = path; }
export function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KiB`;
  if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MiB`;
  return `${(value / 1024 ** 3).toFixed(2)} GiB`;
}
export function shortDigest(value: string) { return value.replace('sha256:', '').slice(0, 12); }
export function dateLabel(value: string) {
  return new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
export const stages = ['validation', 'snapshot', 'inventory', 'structural', 'metadata', 'scanner', 'policy', 'integrity', 'report'];
export const stageLabels: Record<string, string> = {
  validation: 'Validate inputs', snapshot: 'Freeze local snapshot', inventory: 'Record file identities',
  structural: 'Inspect file structure', metadata: 'Collect local declarations', scanner: 'Collect scanner evidence',
  policy: 'Evaluate policy', integrity: 'Recheck artifact identity', report: 'Write private reports', complete: 'Report ready',
};
