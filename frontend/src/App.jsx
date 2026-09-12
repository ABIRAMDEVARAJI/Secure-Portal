import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const PDF_WORKER_URL = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString()

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, { credentials: 'include', ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Request failed')
  }
  if (response.status === 204) return null
  return response.json()
}

function App() {
  const [user, setUser] = useState(undefined)
  useEffect(() => { api('/api/auth/me').then(setUser).catch(() => setUser(null)) }, [])
  if (user === undefined) return <main className="center-state"><span className="spinner" /> Loading your secure workspace...</main>
  if (!user) return <LoginPage />
  return <BrowserRouter><Shell user={user} setUser={setUser} /></BrowserRouter>
}

function LoginPage() {
  return <main className="login-page"><div className="login-art"><span className="eyebrow">PRIVATE KNOWLEDGE LIBRARY</span><h1>Keep the useful things close.</h1><p>A quiet, secure home for the videos, documents, and references your team returns to.</p></div><section className="login-panel"><div className="mark">SC<span>•</span>P</div><p className="eyebrow">SECURE CONTENT PORTAL</p><h2>Welcome back</h2><p className="muted">Sign in with your organization Google account to continue.</p><a className="google-button" href={`${API_URL}/api/auth/login`}><span>G</span> Continue with Google</a><p className="fine-print">Access is managed by your organization. New accounts start as viewers.</p></section></main>
}

function Shell({ user, setUser }) {
  const navigate = useNavigate()
  async function logout() { await api('/api/auth/logout', { method: 'POST' }).catch(() => {}); setUser(null); navigate('/') }
  return <div className="app-shell"><header className="topbar"><Link className="brand" to="/dashboard"><span className="mark">SC<span>•</span>P</span><span>Secure Content Portal</span></Link><nav><Link to="/dashboard">Library</Link>{user.role === 'ADMIN' && <Link to="/admin">Admin desk</Link>}</nav><div className="account"><span className="avatar">{user.name[0]}</span><span className="account-name">{user.name}</span><button className="text-button" onClick={logout}>Sign out</button></div></header><Routes><Route path="/" element={<Navigate to="/dashboard" replace />} /><Route path="/dashboard" element={<Dashboard />} /><Route path="/content/:id" element={<ContentPage />} />{user.role === 'ADMIN' && <><Route path="/admin" element={<AdminPage />} /><Route path="/admin/upload" element={<UploadPage />} /><Route path="/admin/content/:id/edit" element={<EditPage />} /></>}<Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes></div>
}

function Dashboard() {
  const [items, setItems] = useState([]); const [error, setError] = useState('')
  useEffect(() => { api('/api/content').then(setItems).catch((err) => setError(err.message)) }, [])
  return <main className="page"><div className="page-heading"><div><p className="eyebrow">THE LIBRARY</p><h1>Reference, ready when you are.</h1><p className="lede">A curated collection of internal training and trusted material.</p></div></div>{error && <Notice message={error} />}{!error && !items.length ? <div className="empty-state">No content has been published yet.</div> : <div className="content-grid">{items.map((item) => <ContentCard key={item.id} item={item} />)}</div>}</main>
}

function ContentCard({ item }) { return <article className="content-card"><div className={`type-badge ${item.content_type.toLowerCase()}`}>{item.content_type}</div><p className="card-meta">{item.category || 'General'} <span>·</span> {formatSize(item.file_size)}</p><h2>{item.title}</h2><p className="card-description">{item.description || 'No description provided.'}</p><div className="card-footer"><span>{new Date(item.created_at).toLocaleDateString()}</span><Link className="arrow-link" to={`/content/${item.id}`}>Open <span>↗</span></Link></div></article> }

function ContentPage() {
  const { id } = useParams(); const [item, setItem] = useState(null); const [error, setError] = useState('')
  useEffect(() => { api(`/api/content/${id}`).then(setItem).catch((err) => setError(err.message)) }, [id])
  if (error) return <main className="page"><Notice message={error} /></main>
  if (!item) return <main className="center-state"><span className="spinner" /> Opening content...</main>
  return <main className="page detail-page"><Link className="back-link" to="/dashboard">← Back to library</Link><div className="detail-heading"><div><p className="eyebrow">{item.content_type} · {item.category || 'GENERAL'}</p><h1>{item.title}</h1><p className="lede">{item.description}</p></div><span className="detail-date">Added {new Date(item.created_at).toLocaleDateString()}</span></div><ContentViewer item={item} /></main>
}

function ContentViewer({ item }) { if (item.content_type === 'VIDEO') return <video className="media-viewer video-viewer" controls preload="metadata" crossOrigin="use-credentials" src={`${API_URL}/api/content/${item.id}/stream`} />; if (item.content_type === 'PDF') return <PdfViewer id={item.id} />; return <iframe className="html-viewer" title={item.title} sandbox="allow-same-origin" src={`${API_URL}/api/content/${item.id}/html`} /> }

function PdfViewer({ id }) {
  const [pages, setPages] = useState([]); const [error, setError] = useState('')
  useEffect(() => { let active = true; fetch(`${API_URL}/api/content/${id}/pdf`, { credentials: 'include' }).then((response) => { if (!response.ok) throw new Error(`Unable to load PDF (${response.status})`); return response.arrayBuffer() }).then((data) => import('pdfjs-dist').then((pdfjsLib) => { pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL; return pdfjsLib.getDocument({ data }).promise })).then(async (pdf) => { const rendered = []; for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) { const page = await pdf.getPage(pageNumber); const viewport = page.getViewport({ scale: 1.25 }); const canvas = document.createElement('canvas'); canvas.width = viewport.width; canvas.height = viewport.height; await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise; rendered.push(canvas.toDataURL()) } if (active) setPages(rendered) }).catch((err) => active && setError(err.message)); return () => { active = false } }, [id])
  if (error) return <Notice message={error} />; if (!pages.length) return <div className="viewer-loading"><span className="spinner" /> Rendering document...</div>; return <div className="pdf-viewer">{pages.map((page, index) => <img key={page} src={page} alt={`Page ${index + 1}`} />)}</div>
}

function AdminPage() {
  const [items, setItems] = useState([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [query, setQuery] = useState(''); const [type, setType] = useState('ALL')
  async function load() { setLoading(true); setError(''); try { setItems(await api('/api/content')) } catch (err) { setError(err.message) } finally { setLoading(false) } }
  useEffect(() => { let active = true; api('/api/content').then((content) => active && setItems(content)).catch((err) => active && setError(err.message)).finally(() => active && setLoading(false)); return () => { active = false } }, [])
  async function remove(item) { if (!window.confirm(`Delete “${item.title}”? This cannot be undone.`)) return; try { await api(`/api/admin/content/${item.id}`, { method: 'DELETE' }); setItems((current) => current.filter((entry) => entry.id !== item.id)) } catch (err) { setError(err.message) } }
  const visibleItems = items.filter((item) => (type === 'ALL' || item.content_type === type) && `${item.title} ${item.category || ''}`.toLowerCase().includes(query.toLowerCase()))
  return <main className="page"><div className="admin-heading"><div><p className="eyebrow">ADMIN DESK</p><h1>Keep the library useful.</h1><p className="lede">Publish, refine, and retire internal material.</p></div><Link className="primary-button" to="/admin/upload">＋ Upload content</Link></div>{error && <Notice message={error} />}<div className="admin-toolbar"><label className="search-field"><span>Find material</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title or category" /></label><label className="filter-field"><span>Type</span><select value={type} onChange={(event) => setType(event.target.value)}><option value="ALL">All types</option><option value="VIDEO">Video</option><option value="PDF">PDF</option><option value="HTML">HTML</option></select></label><button className="refresh-button" onClick={load} disabled={loading}>{loading ? 'Loading...' : 'Refresh'}</button></div>{loading ? <div className="empty-state"><span className="spinner" />Loading library...</div> : !items.length ? <div className="empty-state">No content has been uploaded yet. Start by adding a file.</div> : !visibleItems.length ? <div className="empty-state">No material matches these filters.</div> : <div className="admin-list">{visibleItems.map((item) => <div className="admin-row" key={item.id}><span className={`type-dot ${item.content_type.toLowerCase()}`} /><div><strong>{item.title}</strong><small>{item.category || 'General'} · {item.content_type} · {formatSize(item.file_size)}</small></div><div className="row-actions"><Link to={`/content/${item.id}`}>View</Link><Link to={`/admin/content/${item.id}/edit`}>Edit</Link><button onClick={() => remove(item)}>Delete</button></div></div>)}</div>}</main>
}

function UploadPage() {
  const navigate = useNavigate(); const [form, setForm] = useState({ title: '', description: '', category: '', file: null }); const [state, setState] = useState({ busy: false, error: '' })
  function update(event) { setForm({ ...form, [event.target.name]: event.target.name === 'file' ? event.target.files[0] : event.target.value }) }
  async function submit(event) { event.preventDefault(); if (!form.file) return setState({ busy: false, error: 'Choose a file to upload.' }); setState({ busy: true, error: '' }); const body = new FormData(); body.append('title', form.title); body.append('description', form.description); body.append('category', form.category); body.append('file', form.file); try { const item = await api('/api/admin/content', { method: 'POST', body }); navigate(`/content/${item.id}`) } catch (err) { setState({ busy: false, error: err.message }) } }
  return <main className="page form-page"><Link className="back-link" to="/admin">← Admin desk</Link><p className="eyebrow">NEW MATERIAL</p><h1>Upload to the library.</h1><p className="lede">Files are checked server-side and stored privately.</p><ContentForm form={form} update={update} submit={submit} state={state} action="Upload content" /></main>
}

function EditPage() {
  const { id } = useParams(); const navigate = useNavigate(); const [form, setForm] = useState(null); const [state, setState] = useState({ busy: false, error: '' })
  useEffect(() => { api(`/api/content/${id}`).then((item) => setForm({ title: item.title, description: item.description || '', category: item.category || '' })).catch((err) => setState({ busy: false, error: err.message })) }, [id])
  if (!form) return <main className="center-state"><span className="spinner" /> Loading content...</main>
  async function submit(event) { event.preventDefault(); setState({ busy: true, error: '' }); try { await api(`/api/admin/content/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) }); navigate(`/content/${id}`) } catch (err) { setState({ busy: false, error: err.message }) } }
  return <main className="page form-page"><Link className="back-link" to="/admin">← Admin desk</Link><p className="eyebrow">EDIT METADATA</p><h1>Refine this material.</h1><ContentForm form={form} update={(event) => setForm({ ...form, [event.target.name]: event.target.value })} submit={submit} state={state} action="Save changes" /></main>
}

function ContentForm({ form, update, submit, state, action }) { return <form className="content-form" onSubmit={submit}><label>Title<input required maxLength="255" name="title" value={form.title} onChange={update} /></label><label>Description<textarea maxLength="5000" name="description" value={form.description} onChange={update} rows="5" /></label><label>Category<input maxLength="100" name="category" value={form.category} onChange={update} /></label>{form.file !== undefined && <label className="file-drop">File<input required type="file" name="file" accept="video/mp4,application/pdf,text/html,.html,.htm" onChange={update} />{form.file && <span>{form.file.name} · {formatSize(form.file.size)}</span>}</label>}{state.error && <Notice message={state.error} />}<button className="primary-button" disabled={state.busy}>{state.busy ? 'Working...' : action}</button></form> }
function Notice({ message }) { return <div className="notice" role="alert">{message}</div> }
function formatSize(bytes) { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB', 'GB']; const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1); return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}` }

export default App