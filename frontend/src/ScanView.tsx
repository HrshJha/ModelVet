import { ArrowLeft, ArrowRight, Check, ChevronRight, FolderOpen, LoaderCircle, ShieldCheck, Square, Upload } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, stageLabels, stages, type Capabilities, type DirectoryPage, type Job, type Policy, type ScanInput } from './api';
import { Badge, Notice, PageHeading } from './components';

export function ScanSetup({ capabilities, initialPath = '', onStarted }: { capabilities: Capabilities | null; initialPath?: string; onStarted: (job: Job) => void }) {
  const [path, setPath] = useState(initialPath);
  const [browsing, setBrowsing] = useState(false);
  const [folder, setFolder] = useState('.');
  const [offset, setOffset] = useState(0);
  const [directories, setDirectories] = useState<DirectoryPage | null>(null);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [policyBusy, setPolicyBusy] = useState(false);
  const file = useRef<HTMLInputElement>(null);
  const [limits, setLimits] = useState({ max_files: 10000, max_file_mib: 1024, max_total_mib: 2048, timeout_sec: 120 });
  const [scanner, setScanner] = useState<'auto' | 'none' | 'modelscan'>('auto');

  useEffect(() => {
    if (!browsing) return;
    const controller = new AbortController();
    setDirectories(null);
    api<DirectoryPage>(`/directories?path=${encodeURIComponent(folder)}&offset=${offset}`, undefined, controller.signal)
      .then(setDirectories).catch(e => { if (!controller.signal.aborted) setError(String(e.message)); });
    return () => controller.abort();
  }, [browsing, folder, offset]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (!path) { setError('Choose a model folder before starting the scan.'); return; }
    setBusy(true);
    try {
      const input: ScanInput = { model_path: path, policy_id: policy?.id || 'default', scanner, ...limits };
      onStarted(await api<Job>('/scans', input));
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }

  async function importPolicy(selected: File | undefined) {
    if (!selected) return;
    setError('');
    if (selected.size > 65536) { setError('Policy files must be no larger than 64 KiB.'); return; }
    setPolicyBusy(true);
    try { setPolicy(await api<Policy>('/policies', { toml: await selected.text() })); }
    catch (e) { setError((e as Error).message); } finally { setPolicyBusy(false); }
  }

  return <>
    <PageHeading eyebrow="LOCAL ARTIFACT ASSESSMENT" title="Start with the evidence." description="Select a model folder. ModelVet inspects its bytes and declarations without loading it." />
    {initialPath && <Notice>Folder preselected from history. Select and confirm the policy before scanning.</Notice>}
    <div className="setup-grid"><form className="panel scan-form" onSubmit={submit}>
      <div className="section-heading"><span className="step-number">01</span><div><h2>Choose your artifact</h2><p>Only folders inside your configured model root are available.</p></div></div>
      <label htmlFor="model-folder">Model folder</label>
      <div className="folder-field"><FolderOpen size={18} /><input id="model-folder" value={path} readOnly placeholder="Choose a local model folder" /><button type="button" className="secondary" onClick={() => { setBrowsing(!browsing); setError(''); }}>Browse folders</button></div>
      <p className="field-hint">Root: <span className="mono">{capabilities?.models_root_label || 'Configured local folder'}</span>. Files stay on this computer.</p>
      {browsing && <section className="folder-browser" aria-label="Model folder browser">
        <div className="folder-browser-head"><button type="button" className="icon-button" aria-label="Parent folder" disabled={folder === '.'} onClick={() => { setFolder(folder.split('/').slice(0, -1).join('/') || '.'); setOffset(0); }}><ArrowLeft size={17} /></button><span className="mono">{folder === '.' ? 'Model root' : folder}</span><button type="button" className="text-button" onClick={() => setBrowsing(false)}>Close</button></div>
        {!directories ? <p className="muted loading-text">Reading directories…</p> : <>
          {directories.entries.length === 0 && <p className="muted loading-text">No child folders. You can select this folder.</p>}
          {directories.entries.map(entry => <button type="button" key={entry.relpath} className="directory-row" disabled={!entry.selectable} onClick={() => { setFolder(entry.relpath); setOffset(0); }}><FolderOpen size={17} /><span>{entry.name}</span>{entry.selectable ? <ChevronRight size={16} /> : <small>Unavailable link or special entry</small>}</button>)}
          {directories.total > 100 && <div className="pagination"><button type="button" disabled={offset === 0} onClick={() => setOffset(offset - 100)}>Previous</button><span>{offset + 1}–{Math.min(offset + 100, directories.total)} of {directories.total}</span><button type="button" disabled={offset + 100 >= directories.total} onClick={() => setOffset(offset + 100)}>Next</button></div>}
        </>}
        <button type="button" className="primary folder-select" onClick={() => { setPath(folder); setBrowsing(false); }}><Check size={15} />Use this folder</button>
      </section>}
      <div className="form-divider" />
      <div className="section-heading"><span className="step-number">02</span><div><h2>Set the review policy</h2><p>Versioned rules determine what evidence is required.</p></div></div>
      <div className="policy-choice"><span className="policy-icon"><ShieldCheck size={20} /></span><div><strong>{policy?.policy_id || 'Conservative default'}</strong><small>{policy ? 'Imported and validated TOML policy' : 'All applicable checks · sourced license and provenance'}</small></div><button type="button" className="text-button" disabled={policyBusy} onClick={() => file.current?.click()}><Upload size={14} />{policyBusy ? 'Validating…' : 'Import TOML'}</button><input ref={file} hidden type="file" accept=".toml" aria-label="Choose policy TOML" onChange={e => void importPolicy(e.target.files?.[0])} /></div>
      {policy && <button type="button" className="text-button reset-policy" onClick={() => setPolicy(null)}>Use default policy instead</button>}
      <details className="advanced"><summary>Advanced scan settings</summary><div className="advanced-grid">{(Object.keys(limits) as (keyof typeof limits)[]).map(key => <label key={key}>{({ max_files: 'Maximum entries', max_file_mib: 'Per file (MiB)', max_total_mib: 'Total input (MiB)', timeout_sec: 'Scanner timeout (seconds)' })[key]}<input type="number" required min={1} max={({ max_files: 10000, max_file_mib: 1024, max_total_mib: 2048, timeout_sec: 120 })[key]} value={limits[key]} onChange={e => setLimits({ ...limits, [key]: Number(e.target.value) })} /></label>)}<label>Scanner<select value={scanner} onChange={e => setScanner(e.target.value as typeof scanner)}><option value="auto">Auto · pinned ModelScan when needed</option><option value="modelscan">ModelScan</option><option value="none">Disabled · required checks stay unresolved</option></select></label></div></details>
      {error && <Notice error>{error}</Notice>}
      <div className="form-footer"><span><ShieldCheck size={14} />Static analysis. No model execution.</span><button className="primary" disabled={busy || policyBusy}>{busy ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}{busy ? 'Starting…' : 'Start scan'}</button></div>
    </form><aside className="setup-aside"><div className="panel aside-note"><p className="eyebrow">WHAT HAPPENS NEXT</p><h3>Every verdict has a trail.</h3><ol><li><span>1</span><div><strong>Freeze the input</strong><p>A private bounded snapshot binds the review to exact file identities.</p></div></li><li><span>2</span><div><strong>Record the evidence</strong><p>Inspect structure, declarations and applicable scanner output.</p></div></li><li><span>3</span><div><strong>Explain the decision</strong><p>See which required checks completed and what remains unresolved.</p></div></li></ol></div>{capabilities && !capabilities.scanner_available && <Notice>ModelScan is not installed on PATH. Safetensors-only reviews can still complete; required serialized-file checks remain unresolved.</Notice>}<p className="fine-print">A scoped approval is specific to the recorded artifact and policy. It does not establish universal safety or legal clearance.</p></aside></div>
  </>;
}

export function ProgressView({ job, connectionError, onCancel }: { job: Job; connectionError: string; onCancel: () => void }) {
  const active = job.status === 'running' || job.status === 'cancelling';
  const position = stages.indexOf(job.stage);
  return <><PageHeading eyebrow="ASSESSMENT IN PROGRESS" title={active ? 'Following the evidence.' : job.status === 'completed' ? 'Your report is ready.' : 'Assessment stopped.'} description={job.label} /><div className="progress-layout"><section className="panel progress-panel"><div className="progress-top"><span className="activity-orb"><LoaderCircle size={27} className={active ? 'spin' : ''} /></span><div><h2>{job.status === 'cancelling' ? 'Stopping and cleaning up…' : stageLabels[job.stage] || job.status}</h2><p className="muted mono">{job.elapsed_seconds.toFixed(1)}s elapsed · {job.status}</p></div>{active && <button className="secondary" disabled={job.status === 'cancelling'} onClick={onCancel}><Square size={13} />Cancel scan</button>}</div><ol className="stage-list">{stages.map((stage, i) => <li key={stage} className={active && i === position ? 'current' : i < position || job.status === 'completed' ? 'done' : ''}><span>{i < position || job.status === 'completed' ? <Check size={14} /> : String(i + 1).padStart(2, '0')}</span><div>{stageLabels[stage]}</div>{active && i === position && <small>In progress</small>}</li>)}</ol><p className="fine-print">These are processing stages, not a safety score. The final report accounts for each applicable required check.</p></section><aside><div className="panel aside-note"><p className="eyebrow">REPRODUCIBLE BY DESIGN</p><h3>Exact input.<br />Explicit policy.<br />Traceable result.</h3><p className="muted">Elapsed time is observed. Completion is never estimated or inferred from an animation.</p></div>{!active && job.status !== 'completed' && <Notice error>No completed report was indexed. {job.error_code ? `Reference: ${job.error_code}.` : 'The scan was cancelled.'}</Notice>}{connectionError && <Notice error>{connectionError} Reconnecting does not change the last recorded job state.</Notice>}</aside></div></>;
}
