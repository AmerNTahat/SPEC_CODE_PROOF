type Data = Record<string, any>;
type Page = "runs" | "setup" | "knowledge" | "review";
declare const ReactDOM: {createRoot(node: Element): {render(node: React.ReactNode): void}};
const fragmentToken = new URLSearchParams(location.hash.slice(1)).get("token");
if (fragmentToken) {sessionStorage.setItem("inspecta-token", fragmentToken); history.replaceState(null, "", location.pathname);}

async function api<T = Data>(path: string, body?: Data): Promise<T> {
  const response = await fetch("/api" + path, {method: body ? "POST" : "GET",
    headers: {"Authorization": "Bearer " + (sessionStorage.getItem("inspecta-token") || ""), "Content-Type": "application/json"},
    body: body ? JSON.stringify(body) : undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data as T;
}
function Details({value, title = "Recorded details"}: {value: unknown; title?: string}) {
  return <details><summary>{title}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}
function App() {
  const [page, setPage] = React.useState<Page>("runs");
  const [overview, setOverview] = React.useState<Data>({runs: [], profiles: [], library_roots: {}, approvals: []});
  const [library, setLibrary] = React.useState<Data>({documents: [], rules: [], counts: {}});
  const [error, setError] = React.useState("");
  const [notice, setNotice] = React.useState("");
  const [token, setToken] = React.useState("");
  const [profileId, setProfileId] = React.useState("");
  const [overrides, setOverrides] = React.useState<Data>({});
  const [step, setStep] = React.useState(0);
  const [resolved, setResolved] = React.useState<Data | null>(null);
  const [runId, setRunId] = React.useState<string | null>(null);
  const [events, setEvents] = React.useState<Data | null>(null);
  const [source, setSource] = React.useState<Data | null>(null);
  const [search, setSearch] = React.useState("");
  const [extensionTokens, setExtensionTokens] = React.useState("");
  const [extensionSeconds, setExtensionSeconds] = React.useState("");
  const [reviewer, setReviewer] = React.useState("");
  const reload = async () => {setOverview(await api("/overview"));};
  async function act(fn: () => Promise<void>) {setError(""); setNotice(""); try {await fn();} catch (e) {setError(String(e));}}
  React.useEffect(() => {void act(reload); const timer = setInterval(() => {void reload().catch(() => {});}, 3000); return () => clearInterval(timer);}, []);
  const profiles: Data[] = overview.profiles;
  const active = profiles.find(p => p.id === profileId) || profiles[0];
  const config = active?.config || {};
  const run: Data | undefined = overview.runs.find((r: Data) => r.id === runId);
  const mode = overrides.mode || config.mode || "user";
  const budget = {...overview.defaults?.[mode]?.budget, ...config.budget, ...overrides.budget};
  const request = {profile_id: active?.id, overrides};
  function change(key: string, value: unknown) {setOverrides({...overrides, [key]: value}); setResolved(null);}
  async function loadLibrary() {setLibrary(await api("/library")); setPage("knowledge");}
  async function prepare() {const result = await api("/runs", request); setRunId(result.id); setPage("runs"); await reload(); setNotice("Prepared an isolated input snapshot. No tools or models were launched.");}
  const tabs: [Page, string][] = [["runs", "Runs & evidence"], ["setup", "New workflow"], ["knowledge", "Knowledge library"], ["review", "Review queue"]];
  return <div className="shell">
    <aside><div className="brand">INSPECTA<span>SCP WORKBENCH</span></div><nav aria-label="Workspace">{tabs.map(([key, label]) =>
      <button key={key} aria-current={page === key ? "page" : undefined} onClick={() => key === "knowledge" ? void act(loadLibrary) : setPage(key)}>{label}</button>)}</nav>
      <div className="host">Execution host<br/><strong>This computer</strong><p>Local workspace · paid demonstrations deferred</p></div></aside>
    <main><header><div><span className="eyebrow">ENGINEERING WORKSPACE</span><h1>{tabs.find(t => t[0] === page)?.[1]}</h1></div><span className="badge">Implementation in progress</span></header>
      <div role="status" aria-live="polite">{notice && <p className="notice">{notice}</p>}</div>
      {error && <div role="alert" className="error">{error}<details><summary>Reconnect to this local session</summary><label>Session token<input type="password" value={token} onChange={e => setToken(e.target.value)}/></label><button onClick={() => {sessionStorage.setItem("inspecta-token", token); setToken(""); void act(reload);}}>Connect</button></details></div>}
      <p className="boundary">Tool checks, formal verification, and engineering acceptance are separate results. Paid model execution is disabled.</p>
      {page === "setup" && <section className="card"><ol className="steps">{["Materials", "Workflow", "Budget", "Review"].map((s, i) => <li key={s} aria-current={step === i ? "step" : undefined}>{i + 1}. {s}</li>)}</ol>
        {step === 0 && <><h2>Select an inspected project</h2><label>Saved project profile<select value={active?.id || ""} onChange={e => {setProfileId(e.target.value); setOverrides({}); setResolved(null);}}>{profiles.map(p => <option key={p.id}>{p.id}</option>)}</select></label><p>Source files are copied to a separate run workspace. Your existing project stays in place.</p><Details title="Input paths and allowed files" value={{project: config.project, input_files: config.input_files}}/></>}
        {step === 1 && <><h2>Choose the work</h2><div className="grid"><label>Workflow mode<select value={mode} onChange={e => change("mode", e.target.value)}><option value="user">User — apply frozen knowledge</option><option value="learning">Learning — develop knowledge</option></select></label><label>Assistance<select value={overrides.assistance || config.assistance || "automatic"} onChange={e => change("assistance", e.target.value)}><option value="automatic">Automatic</option><option value="interactive">Interactive</option></select></label></div><label>Operation<select value={overrides.task_operation || config.task_operation || "auto"} onChange={e => change("task_operation", e.target.value)}>{["auto", "continue-project", "complete-system", "extend-system", "repair-system", "verify-only", "create-system"].map(s => <option key={s}>{s}</option>)}</select></label><p>Only verification is executable in this build. Creation requires a separately authorized profile; choosing it cannot grant permission.</p></>}
        {step === 2 && <><h2>Set aggregate limits</h2><p>These are caps, not completion-time estimates. Pausing does not reset the deadline.</p><div className="grid"><label>Wall-clock seconds<input type="number" min="1" value={budget.wall_seconds} onChange={e => change("budget", {...overrides.budget, wall_seconds: Number(e.target.value)})}/></label><label>Aggregate model tokens<input type="number" min="1" value={budget.aggregate_model_tokens} onChange={e => change("budget", {...overrides.budget, aggregate_model_tokens: Number(e.target.value)})}/></label></div><p>Strict token-cap enforcement is not validated for Codex CLI. No model calls will be launched.</p></>}
        {step === 3 && <><h2>Review the resolved request</h2><p>Only deliberate changes override the saved profile. The backend resolves and hashes the same configuration as the CLI.</p><button onClick={() => void act(async () => {setResolved(await api("/resolve", request));})}>Resolve configuration</button>{resolved && <><p className="hash">Configuration SHA-256: {resolved.config_sha256}</p><Details value={resolved.config}/><button className="primary" onClick={() => void act(prepare)}>Prepare run</button></>}</>}
        <div className="actions"><button disabled={step === 0} onClick={() => setStep(step - 1)}>Back</button><button disabled={step === 3 || !active} onClick={() => setStep(step + 1)}>Next</button></div></section>}
      {page === "runs" && <><div className="grid"><section className="card"><h2>Recorded runs</h2>{!overview.runs.length && <p>No runs yet. Prepare a workflow to inspect its inputs and limits.</p>}{overview.runs.map((r: Data) => <button className="run" key={r.id} onClick={() => {setRunId(r.id); setEvents(null);}}><strong>{r.config.resolved_operation}</strong><span>{r.id.slice(0, 12)} · {r.state}</span>{r.source_changed?.length > 0 && <span>STALE — source changed</span>}</button>)}</section>
      <section className="card"><h2>{run ? "Run details" : "Select a run"}</h2>{run && <><p className="hash">{run.id}</p><span className="badge">{run.state}</span><dl><dt>Remaining time</dt><dd>{Math.floor(run.remaining_seconds)} seconds</dd><dt>Known model tokens</dt><dd>{run.usage_unknown ? "Unknown — further calls blocked" : run.used_tokens}</dd><dt>Project readiness</dt><dd>{run.result?.project_status || "NOT_ASSESSED"}</dd></dl><div className="actions">{["execute", "pause", "resume", "stop"].map(action => <button key={action} disabled={action === "execute" ? run.state !== "READY" : action === "resume" ? run.state !== "PAUSED" : !["READY", "CHECKING", "RUNNING", "PAUSED"].includes(run.state)} onClick={() => void act(async () => {const r = await api(`/runs/${run.id}/${action}`, {}); setNotice(r.status || r.state); await reload();})}>{action === "execute" ? "Run checks" : action}</button>)}</div>{run.result?.gates?.map((g: Data) => <div className="gate" key={g.gate}><strong>{g.gate}: {g.status}</strong><p>{g.reason}</p></div>)}<button onClick={() => void act(async () => {setEvents(await api(`/runs/${run.id}/logs`));})}>View recorded events</button>{events && <Details title="Commands, state transitions and evidence references" value={events}/>}<details><summary>Request a budget extension</summary><p>Enter new total caps. Usage and elapsed time are retained; a reviewed extension never authorizes paid execution.</p><label>Total tokens<input type="number" min={run.config.budget.aggregate_model_tokens} value={extensionTokens} onChange={e => setExtensionTokens(e.target.value)}/></label><label>Total wall-clock seconds<input type="number" min={run.config.budget.wall_seconds} value={extensionSeconds} onChange={e => setExtensionSeconds(e.target.value)}/></label><button disabled={!extensionTokens || !extensionSeconds} onClick={() => void act(async () => {await api(`/runs/${run.id}/budget`, {aggregate_model_tokens: Number(extensionTokens), wall_seconds: Number(extensionSeconds)}); await reload(); setPage("review");})}>Request review</button></details><Details title="Resolved configuration" value={run.config}/></>}</section></div></>}
      {page === "knowledge" && <><section className="card"><h2>Import existing books</h2><p>Original wording, IDs, confidence fields and source hashes are preserved. Import does not approve a rule.</p><div className="actions">{Object.entries(overview.library_roots).map(([id, path]) => <button key={id} onClick={() => void act(async () => {const r = await api("/library/import", {root_id: id}); setNotice(`Imported ${r.document_count} documents; originals unchanged.`); await loadLibrary();})}>Import {String(path).split("/").pop()}</button>)}</div><p>{library.counts.documents || 0} documents · {library.counts.rule_ids || 0} rule IDs · {library.counts.conflicting_ids || 0} IDs needing conflict review</p><label>Find a rule<input value={search} onChange={e => setSearch(e.target.value)} placeholder="Rule ID or wording"/></label></section>
        <div className="grid"><section className="card"><h2>Rules and provenance</h2>{library.rules.filter((r: Data) => JSON.stringify(r).toLowerCase().includes(search.toLowerCase())).map((r: Data) => <details key={r.rule_id}><summary>{r.rule_id} · {r.status}</summary>{r.variants.map((v: Data) => <div key={v.id}><p>Original forecast: {v.original_forecast.score ?? "Not recorded"} — not measured success.</p><Details value={v.record} title="Preserved original record"/></div>)}<p>Source documents</p>{r.documents.map((id: string) => {const doc = library.documents.find((d: Data) => d.id === id); return doc && <button className="source-link" key={id} onClick={() => void act(async () => {setSource(await api(`/source/${doc.source_id}`));})}>{doc.path}</button>;})}</details>)}</section>
        <section className="card"><h2>Exact source revision</h2>{source ? <><span className="badge">{source.freshness}</span><p>{source.relative} · lines {source.start_line}–{source.end_line}</p><p className="hash">SHA-256 {source.sha256}</p><p>Human review only; viewing does not export source material to a model.</p><pre className="source-text">{source.text}</pre></> : <p>Select a source link from a rule to inspect the recorded text.</p>}</section></div></>}
      {page === "review" && <section className="card"><h2>Exact-subject review</h2><p>A decision applies only to the displayed digest. Approval cannot waive missing engineering checks.</p><label>Reviewer name or review record<input value={reviewer} onChange={e => setReviewer(e.target.value)}/></label>{!overview.approvals.length && <p>No approval requests.</p>}{overview.approvals.map((a: Data) => <article key={a.id}><h3>{a.action} · {a.status}</h3><p className="hash">{a.subject_digest}</p><Details value={a.subject} title="Inspect exact requested scope"/><div className="actions">{(a.status === "PENDING" ? ["APPROVED", "REJECTED"] : a.status === "APPROVED" ? ["REVOKED"] : []).map(decision => <button key={decision} disabled={!reviewer.trim()} onClick={() => void act(async () => {await api(`/approvals/${a.id}`, {decision, reviewer, expected_digest: a.subject_digest}); await reload();})}>{decision}</button>)}{a.status === "APPROVED" && a.action === "increase_budget" && <button onClick={() => void act(async () => {const r = await api(`/runs/${a.subject.run_id}/budget`, {approval_id: a.id}); setRunId(r.id); setPage("runs"); await reload(); setNotice("Approved caps applied. Run remains paused; prior usage is retained.");})}>Apply approved extension</button>}</div></article>)}</section>}
    </main></div>;
}
ReactDOM.createRoot(document.getElementById("root")!).render(<App/>);
