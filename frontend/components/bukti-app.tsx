'use client'

import { useRef, useState, type CSSProperties, type ReactNode } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bell,
  BookOpen,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Clock3,
  Download,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  Image as ImageIcon,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  Zap,
} from 'lucide-react'

type Screen = 'cases' | 'create' | 'intake' | 'overview' | 'questions' | 'detail' | 'actions' | 'export'
type Status = 'SUPPORTED' | 'PARTIAL' | 'MISSING' | 'CONFLICT' | 'OUTDATED' | 'UNSUPPORTED'

const questions: {
  id: string
  q: string
  topic: string
  evidence: Status
  review: string
  priority: number
  reason: string
}[] = [
  { id: 'Q-E-01', q: 'Report annual electricity consumption.', topic: 'Energy', evidence: 'PARTIAL', review: 'UNREVIEWED', priority: 82, reason: 'Only 3 of 12 months are supported' },
  { id: 'Q-E-02', q: 'What percentage of waste was recycled?', topic: 'Waste', evidence: 'CONFLICT', review: 'NEEDS REVIEW', priority: 78, reason: 'Two sources report different recycling rates' },
  { id: 'Q-E-03', q: 'Describe your environmental policy.', topic: 'Policy', evidence: 'SUPPORTED', review: 'CONFIRMED', priority: 28, reason: 'Current signed policy found' },
  { id: 'Q-S-01', q: 'Report workforce injury frequency.', topic: 'Health & safety', evidence: 'MISSING', review: 'UNREVIEWED', priority: 75, reason: 'Incident register not uploaded' },
  { id: 'Q-S-02', q: 'Describe employee grievance channels.', topic: 'People', evidence: 'OUTDATED', review: 'NEEDS REVIEW', priority: 67, reason: 'Policy review date passed' },
  { id: 'Q-G-01', q: 'Who oversees ESG responsibilities?', topic: 'Governance', evidence: 'SUPPORTED', review: 'CONFIRMED', priority: 31, reason: 'Board charter and minutes align' },
  { id: 'Q-G-02', q: 'Describe anti-bribery controls.', topic: 'Ethics', evidence: 'UNSUPPORTED', review: 'UNREVIEWED', priority: 62, reason: 'Draft has no linked evidence' },
  { id: 'Q-G-03', q: 'Report whistleblowing cases.', topic: 'Ethics', evidence: 'SUPPORTED', review: 'UNREVIEWED', priority: 42, reason: 'Register supports zero cases' },
]

const docs = [
  ['tnb-bills-jan-mar-2025.pdf', 'Utility bill', 'READY', '3 questions'],
  ['environmental-policy-v3.pdf', 'Policy', 'READY', '2 questions'],
  ['waste-tracker-2025.xlsx', 'Spreadsheet', 'REVIEW', 'Conflict found'],
  ['employee-handbook-2023.docx', 'Policy', 'OUTDATED', '1 question'],
  ['incident-register-scan.pdf', 'Scanned PDF', 'FAILED', 'Needs manual review'],
]

type FileKind = 'pdf' | 'image' | 'spreadsheet' | 'doc' | 'other'

type EvidenceItem = {
  id: string
  name: string
  type: string
  status: string
  coverage: string
  uploadedLabel: string
  kind: FileKind
  url?: string
  size?: number
}

function getFileKind(name: string, mime = ''): FileKind {
  const lower = name.toLowerCase()
  if (mime === 'application/pdf' || lower.endsWith('.pdf')) return 'pdf'
  if (mime.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg)$/.test(lower)) return 'image'
  if (/\.(xlsx?|csv)$/.test(lower) || mime.includes('spreadsheet')) return 'spreadsheet'
  if (/\.(docx?|txt|rtf)$/.test(lower) || mime.includes('word')) return 'doc'
  return 'other'
}

function kindLabel(kind: FileKind) {
  switch (kind) {
    case 'pdf':
      return 'PDF document'
    case 'image':
      return 'Image'
    case 'spreadsheet':
      return 'Spreadsheet'
    case 'doc':
      return 'Word document'
    default:
      return 'Document'
  }
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

let uploadCounter = 0

function fileToEvidenceItem(file: File): EvidenceItem {
  uploadCounter += 1
  const kind = getFileKind(file.name, file.type)
  return {
    id: `upload-${Date.now()}-${uploadCounter}`,
    name: file.name,
    type: kindLabel(kind),
    status: 'PROCESSING',
    coverage: 'Pending review',
    uploadedLabel: 'Just now',
    kind,
    url: URL.createObjectURL(file),
    size: file.size,
  }
}

function seedEvidenceItems(): EvidenceItem[] {
  return docs.map(([name, type, status, coverage]) => ({
    id: `seed-${name}`,
    name,
    type,
    status,
    coverage,
    uploadedLabel: 'Today, 10:24',
    kind: getFileKind(name),
  }))
}

function FileKindIcon({ kind }: { kind: FileKind }) {
  if (kind === 'image') return <ImageIcon />
  if (kind === 'spreadsheet') return <FileSpreadsheet />
  return <FileText />
}

function formatStatus(value: string) {
  return value
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function toneOf(value: string) {
  return value.toLowerCase().replace(/\s+/g, '-')
}

function Mark() {
  return (
    <div className="mark" aria-hidden="true">
      <ShieldCheck />
    </div>
  )
}

function Pill({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className={`pill ${tone}`}>{children}</span>
}

function StatusPill({ value }: { value: string }) {
  return <Pill tone={toneOf(value)}>{formatStatus(value)}</Pill>
}

function Meter({ value }: { value: number }) {
  return (
    <div className="meter" aria-label={`${value}% complete`}>
      <span style={{ width: `${value}%` }} />
    </div>
  )
}

function SearchField({ placeholder, grow = false }: { placeholder: string; grow?: boolean }) {
  return (
    <label className={`input${grow ? ' grow' : ''}`}>
      <Search />
      <input type="search" placeholder={placeholder} />
    </label>
  )
}

function Header({ onMenu }: { onMenu: () => void }) {
  return (
    <>
      <header className="topbar">
        <button className="icon-btn mobile-menu" onClick={onMenu} aria-label="Open navigation" type="button">
          <Menu />
        </button>
        <div className="crumb">
          Cases <span>/</span> Major Customer ESG Questionnaire 2026
        </div>
        <div className="top-actions">
          <button className="search" type="button">
            <Search />
            <span>Search evidence</span>
            <kbd>⌘ K</kbd>
          </button>
          <Pill tone="warning">
            <Clock3 />
            13 days left
          </Pill>
          <button className="review-btn" type="button">
            <ClipboardCheck />
            Review queue
            <b>5</b>
          </button>
          <button className="icon-btn" aria-label="Notifications" type="button">
            <Bell />
          </button>
          <div className="avatar" aria-label="Nur Aina">
            NA
          </div>
        </div>
      </header>
      <div className="prototype">
        <Sparkles />
        Prototype workspace · Synthetic, de-identified demo data only · Not an audit or certification
      </div>
    </>
  )
}

const nav = [
  ['cases', 'Cases', BriefcaseBusiness],
  ['overview', 'Overview', LayoutDashboard],
  ['questions', 'Questionnaire', BookOpen],
  ['intake', 'Evidence', FolderOpen],
  ['actions', 'Actions', ClipboardCheck],
  ['export', 'Export', Download],
] as const

function Sidebar({
  screen,
  setScreen,
  collapsed,
  setCollapsed,
  open,
}: {
  screen: Screen
  setScreen: (s: Screen) => void
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  open: boolean
}) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${open ? 'open' : ''}`}>
      <div className="brand">
        <Mark />
        <div>
          <strong>BuktiESG</strong>
          <small>Evidence operations</small>
        </div>
      </div>
      <div className="case-step">Response workflow · 13 days</div>
      <nav>
        {nav.map(([id, label, Icon]) => {
          const active = screen === id || (screen === 'detail' && id === 'questions')
          return (
            <button
              key={id}
              type="button"
              className={active ? 'active' : ''}
              onClick={() => setScreen(id)}
              title={label}
              aria-current={active ? 'page' : undefined}
              aria-label={label === 'Questionnaire' ? 'Questionnaire, 5 items' : label}
            >
              <Icon />
              <span>{label}</span>
              {label === 'Questionnaire' && <em>5</em>}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace">
          <div className="avatar small">BP</div>
          <div>
            <b>BuktiPack Manufacturing</b>
            <small>Selangor · 45 employees</small>
          </div>
        </div>
        <button className="collapse" type="button" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
          <span>Collapse sidebar</span>
        </button>
      </div>
    </aside>
  )
}

function PageTitle({
  eyebrow,
  title,
  desc,
  actions,
}: {
  eyebrow?: string
  title: string
  desc: string
  actions?: ReactNode
}) {
  return (
    <div className="page-title">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        <p>{desc}</p>
      </div>
      {actions && <div className="title-actions">{actions}</div>}
    </div>
  )
}

function Summary({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub: string
  tone?: string
}) {
  return (
    <div className="summary">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
      <small>{sub}</small>
    </div>
  )
}

function Cases({ go }: { go: (s: Screen) => void }) {
  return (
    <div>
      <PageTitle
        eyebrow="Workspace"
        title="Response cases"
        desc="Manage customer ESG requests, evidence, owners and deadlines."
        actions={
          <button className="primary" type="button" onClick={() => go('create')}>
            <Plus />
            New case
          </button>
        }
      />
      <div className="summary-grid">
        <Summary label="Active cases" value="3" sub="Across two customers" />
        <Summary label="Due soon" value="1" sub="Within the next 14 days" tone="warn-text" />
        <Summary label="Required confirmed" value="18 / 29" sub="Across active cases" />
        <Summary label="Open actions" value="9" sub="4 high priority" tone="warn-text" />
      </div>
      <div className="toolbar">
        <SearchField placeholder="Search cases" />
        <button className="control" type="button">
          All status
          <ChevronDown />
        </button>
        <button className="control" type="button">
          Due date
          <ChevronDown />
        </button>
      </div>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Customer</th>
              <th>Readiness</th>
              <th>Due</th>
              <th>Owner</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr className="clickable urgent" onClick={() => go('overview')}>
              <td>
                <div className="cell-title">
                  <span className="file-icon">
                    <FileSpreadsheet />
                  </span>
                  <div>
                    <b>Major Customer ESG Questionnaire 2026</b>
                    <small>20 questions · 12 required</small>
                  </div>
                </div>
              </td>
              <td>Demo FMCG Customer</td>
              <td>
                <b>58%</b>
                <Meter value={58} />
                <small>7 of 12 confirmed</small>
              </td>
              <td>
                <b className="warn-text">4 Sep 2026</b>
                <small>13 days left</small>
              </td>
              <td>
                <div className="person">
                  <span>NA</span>
                  Nur Aina
                </div>
              </td>
              <td>
                <Pill tone="warning">In progress</Pill>
              </td>
              <td>
                <ArrowRight />
              </td>
            </tr>
            <tr>
              <td>
                <div className="cell-title">
                  <span className="file-icon">
                    <FileText />
                  </span>
                  <div>
                    <b>Supplier Code Review 2026</b>
                    <small>14 questions · 9 required</small>
                  </div>
                </div>
              </td>
              <td>Regional Retail Group</td>
              <td>
                <b>78%</b>
                <Meter value={78} />
                <small>7 of 9 confirmed</small>
              </td>
              <td>
                <b>18 Sep 2026</b>
                <small>27 days left</small>
              </td>
              <td>
                <div className="person">
                  <span>FM</span>
                  Farid M.
                </div>
              </td>
              <td>
                <Pill tone="partial">In review</Pill>
              </td>
              <td>
                <MoreHorizontal />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

function CreateCase({ go }: { go: (s: Screen) => void }) {
  const [step, setStep] = useState(1)
  const steps = ['Case details', 'Reporting scope', 'Questionnaire', 'Review']

  return (
    <div className="narrow">
      <button className="back" type="button" onClick={() => go('cases')}>
        <ArrowLeft />
        Back to cases
      </button>
      <PageTitle
        eyebrow={`New case · Step ${step} of 4`}
        title="Create a response case"
        desc="Set up the customer request, reporting boundary and initial files."
      />
      <div className="steps">
        {steps.map((label, i) => (
          <div className={i + 1 <= step ? 'done' : ''} key={label}>
            <span>{i + 1 < step ? <Check /> : i + 1}</span>
            {label}
          </div>
        ))}
      </div>
      <section className="form-card">
        {step === 1 && (
          <>
            <h2>Case details</h2>
            <label>
              Case title
              <input defaultValue="Major Customer ESG Questionnaire 2026" />
            </label>
            <div className="form-grid">
              <label>
                Customer
                <input defaultValue="Demo FMCG Customer" />
              </label>
              <label>
                Due date
                <input type="date" defaultValue="2026-09-04" />
              </label>
            </div>
            <label>
              Internal owner
              <select defaultValue="Nur Aina">
                <option>Nur Aina</option>
                <option>Finance Manager</option>
              </select>
            </label>
          </>
        )}
        {step === 2 && (
          <>
            <h2>Reporting scope</h2>
            <div className="form-grid">
              <label>
                Period start
                <input type="date" defaultValue="2025-01-01" />
              </label>
              <label>
                Period end
                <input type="date" defaultValue="2025-12-31" />
              </label>
            </div>
            <label>
              Entity
              <input defaultValue="BuktiPack Manufacturing Sdn. Bhd." />
            </label>
            <label>
              Site
              <input defaultValue="Selangor manufacturing site" />
            </label>
          </>
        )}
        {step === 3 && (
          <>
            <h2>Questionnaire</h2>
            <div className="dropzone">
              <UploadCloud />
              <b>Drop customer questionnaire here</b>
              <span>PDF, DOCX, XLSX or CSV · Maximum 25 MB</span>
              <button className="secondary" type="button">
                Choose file
              </button>
            </div>
            <div className="uploaded">
              <FileSpreadsheet />
              <div>
                <b>customer-esg-questionnaire-2026.xlsx</b>
                <small>428 KB · 20 questions detected</small>
              </div>
              <Check />
            </div>
          </>
        )}
        {step === 4 && (
          <>
            <h2>Review case setup</h2>
            <div className="review-list">
              <Key label="Customer" value="Demo FMCG Customer" />
              <Key label="Reporting period" value="1 Jan – 31 Dec 2025" />
              <Key label="Questionnaire" value="20 questions · 12 required" />
              <Key label="Due date" value="4 Sep 2026" />
            </div>
            <div className="callout info">
              <CircleHelp />
              <div>
                <b>Nothing will be submitted to your customer</b>
                <p>This creates an internal response workspace only.</p>
              </div>
            </div>
          </>
        )}
        <div className="form-actions">
          <button className="secondary" type="button" disabled={step === 1} onClick={() => setStep(step - 1)}>
            Back
          </button>
          {step < 4 ? (
            <button className="primary" type="button" onClick={() => setStep(step + 1)}>
              Continue
              <ArrowRight />
            </button>
          ) : (
            <button className="primary" type="button" onClick={() => go('intake')}>
              <Check />
              Create case
            </button>
          )}
        </div>
      </section>
    </div>
  )
}

const ACCEPTED_EVIDENCE_TYPES =
  '.pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.gif,.webp,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,image/*'

function Intake() {
  const [items, setItems] = useState<EvidenceItem[]>(() => seedEvidenceItems())
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const selected = items.find((item) => item.id === selectedId) ?? null
  const issueCount = items.filter((item) => item.status === 'FAILED' || item.status === 'REVIEW').length

  function addFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList)
    if (files.length === 0) return
    const next = files.map(fileToEvidenceItem)
    setItems((prev) => [...next, ...prev])
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files)
  }

  return (
    <div>
      <PageTitle
        eyebrow="Evidence intake"
        title="Documents & evidence"
        desc="Upload and inspect the files used to support questionnaire answers."
        actions={
          <button className="primary" type="button" onClick={() => inputRef.current?.click()}>
            <UploadCloud />
            Upload evidence
          </button>
        }
      />
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EVIDENCE_TYPES}
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files) addFiles(e.target.files)
          e.target.value = ''
        }}
      />
      <div
        className={`dropzone compact clickable${dragActive ? ' active' : ''}`}
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        <UploadCloud />
        <div>
          <b>Drop supporting documents here</b>
          <span>Documents, images or spreadsheets · PDF, DOCX, XLSX, CSV, JPG, PNG</span>
        </div>
      </div>
      <div className="section-head">
        <div>
          <h2>Evidence library</h2>
          <p>
            {items.length} file{items.length === 1 ? '' : 's'} · {issueCount} issue{issueCount === 1 ? '' : 's'}{' '}
            require attention
          </p>
        </div>
        <button className="control" type="button">
          All files
          <ChevronDown />
        </button>
      </div>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Processing</th>
              <th>Linked coverage</th>
              <th>Uploaded</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="clickable" onClick={() => setSelectedId(item.id)}>
                <td>
                  <div className="cell-title">
                    <span className="file-icon">
                      <FileKindIcon kind={item.kind} />
                    </span>
                    <div>
                      <b>{item.name}</b>
                      <small>{item.size ? formatBytes(item.size) : 'Synthetic demonstration file'}</small>
                    </div>
                  </div>
                </td>
                <td>{item.type}</td>
                <td>
                  <StatusPill value={item.status} />
                </td>
                <td>{item.coverage}</td>
                <td>{item.uploadedLabel}</td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && (
          <div className="empty">
            <UploadCloud />
            <b>No evidence uploaded yet</b>
            <span>Drop files above or browse to upload supporting documents.</span>
          </div>
        )}
      </div>
      {selected && <EvidencePreviewDrawer item={selected} close={() => setSelectedId(null)} />}
    </div>
  )
}

function EvidencePreviewDrawer({ item, close }: { item: EvidenceItem; close: () => void }) {
  const [openOriginal, setOpenOriginal] = useState(false)

  return (
    <Drawer title={item.name} close={close}>
      {item.kind === 'image' && item.url ? (
        <div className="doc-preview image-preview">
          <img src={item.url} alt={`Preview of ${item.name}`} />
        </div>
      ) : item.kind === 'pdf' && item.url ? (
        <div className="doc-preview pdf-frame">
          <iframe src={item.url} title={`Preview of ${item.name}`} />
        </div>
      ) : (
        <div className="doc-preview">
          <FileKindIcon kind={item.kind} />
          <b>Evidence preview</b>
          <span>{item.url ? 'Preview not available for this file type' : 'Extracted text and source locations'}</span>
        </div>
      )}
      <Key label="Type" value={item.type} />
      <Key label="Processing" value={item.url ? 'Uploaded · awaiting parse' : 'Parsed text · 4 pages'} />
      <Key label="Coverage" value={item.coverage} />
      {item.size ? <Key label="Size" value={formatBytes(item.size)} /> : null}
      {item.url ? (
        <a
          className="primary full"
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => setOpenOriginal(true)}
        >
          Open original {item.kind === 'pdf' ? 'PDF' : 'file'}
        </a>
      ) : (
        <button className="primary full" type="button">
          Open source preview
        </button>
      )}
      {openOriginal && (
        <p className="preview-hint">
          <CircleHelp />
          Opened in a new tab. Synthetic demo file only.
        </p>
      )}
    </Drawer>
  )
}

function Overview({ go }: { go: (s: Screen) => void }) {
  return (
    <div>
      <PageTitle
        eyebrow="Major Customer ESG Questionnaire 2026"
        title="Response readiness"
        desc="See what is proven, what needs review, and what must happen next."
        actions={
          <button className="primary" type="button" onClick={() => go('questions')}>
            Open questionnaire
            <ArrowRight />
          </button>
        }
      />
      <div className="readiness">
        <div className="score">
          <div className="ring" style={{ '--p': 58 } as CSSProperties}>
            <div className="ring-inner">
              <strong>58%</strong>
              <span>ready</span>
            </div>
          </div>
          <div>
            <Pill tone="warning">13 days left</Pill>
            <h2>7 of 12 required answers confirmed</h2>
            <p>Five required answers still need evidence or human review before export.</p>
            <Meter value={58} />
          </div>
        </div>
        <div className="readiness-stats">
          <Summary label="Confirmed" value="7" sub="Required answers" />
          <Summary label="Unconfirmed drafts" value="5" sub="Human review needed" />
          <Summary label="Open actions" value="4" sub="2 due this week" />
        </div>
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Readiness by pillar</h2>
              <p>Required questions only</p>
            </div>
          </div>
          {([
            ['Environmental', 46, '2 confirmed'],
            ['Social', 67, '2 confirmed'],
            ['Governance', 75, '3 confirmed'],
          ] as const).map(([name, value, note]) => (
            <div className="pillar" key={name}>
              <div className="pillar-icon">{name[0]}</div>
              <div>
                <b>{name}</b>
                <small>{note}</small>
              </div>
              <Meter value={value} />
              <strong>{value}%</strong>
            </div>
          ))}
        </section>
        <section className="panel priorities">
          <div className="section-head">
            <div>
              <h2>Highest priorities</h2>
              <p>Based on requirement, evidence risk and deadline</p>
            </div>
            <button className="link" type="button" onClick={() => go('questions')}>
              View all
            </button>
          </div>
          {questions.slice(0, 4).map((q) => (
            <button key={q.id} type="button" onClick={() => go(q.id === 'Q-E-01' ? 'detail' : 'questions')}>
              <span className="priority-score">{q.priority}</span>
              <div>
                <b>{q.q}</b>
                <small>
                  {q.id} · {q.reason}
                </small>
              </div>
              <ArrowRight />
            </button>
          ))}
        </section>
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Evidence coverage</h2>
              <p>Across all 20 questions</p>
            </div>
          </div>
          <div className="coverage">
            <div>
              <span className="supported">9</span>
              <small>Supported</small>
            </div>
            <div>
              <span className="partial">4</span>
              <small>Partial</small>
            </div>
            <div>
              <span className="missing">5</span>
              <small>Missing</small>
            </div>
            <div>
              <span className="conflict">2</span>
              <small>Conflict</small>
            </div>
          </div>
          <div className="callout warning">
            <AlertTriangle />
            <div>
              <b>1 processing issue</b>
              <p>Incident register scan needs manual review.</p>
            </div>
            <button className="link" type="button" onClick={() => go('intake')}>
              Inspect
            </button>
          </div>
        </section>
        <section className="panel activity">
          <div className="section-head">
            <div>
              <h2>Recent activity</h2>
              <p>Latest workspace changes</p>
            </div>
          </div>
          {[
            ['NA', 'Nur Aina confirmed Q-G-01', '18 min ago'],
            ['FM', 'Finance Manager uploaded utility bills', '42 min ago'],
            ['BK', 'BuktiESG found a source conflict', '1 hr ago'],
          ].map(([initials, text, time]) => (
            <div key={text}>
              <span>{initials}</span>
              <p>
                <b>{text}</b>
                <small>{time}</small>
              </p>
            </div>
          ))}
        </section>
      </div>
    </div>
  )
}

function Questions({ go }: { go: (s: Screen) => void }) {
  const [filter, setFilter] = useState('All')
  const filters = [
    ['All', 'All'],
    ['PARTIAL', 'Partial'],
    ['MISSING', 'Missing'],
    ['CONFLICT', 'Conflict'],
  ] as const
  const list = filter === 'All' ? questions : questions.filter((q) => q.evidence === filter)

  return (
    <div>
      <PageTitle
        eyebrow="Question workbench"
        title="Customer questionnaire"
        desc="20 questions · 12 required · Separate evidence from human review."
        actions={
          <button className="secondary" type="button">
            <Download />
            Export list
          </button>
        }
      />
      <div className="summary-strip">
        <b>
          7 <span>confirmed required</span>
        </b>
        <b>
          5 <span>unconfirmed drafts</span>
        </b>
        <b>
          4 <span>open evidence gaps</span>
        </b>
        <b>
          2 <span>source conflicts</span>
        </b>
      </div>
      <div className="toolbar">
        <SearchField placeholder="Search questions" grow />
        {filters.map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={`filter${filter === value ? ' active' : ''}`}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
        <button className="control" type="button">
          Priority
          <ChevronDown />
        </button>
      </div>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Question</th>
              <th>Topic</th>
              <th>Evidence</th>
              <th>Review</th>
              <th>Reason</th>
              <th>Priority</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((q) => (
              <tr key={q.id} className="clickable" onClick={() => go('detail')}>
                <td>
                  <div className="question-cell">
                    <span>{q.id}</span>
                    <b>{q.q}</b>
                    <small>{['Q-E-01', 'Q-S-01', 'Q-G-02'].includes(q.id) ? 'Required' : 'Optional'}</small>
                  </div>
                </td>
                <td>{q.topic}</td>
                <td>
                  <StatusPill value={q.evidence} />
                </td>
                <td>
                  <StatusPill value={q.review} />
                </td>
                <td className="reason">
                  <AlertTriangle />
                  <span>{q.reason}</span>
                </td>
                <td>
                  <strong className="priority-score">{q.priority}</strong>
                </td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && (
          <div className="empty">
            <Search />
            <b>No questions match these filters</b>
            <span>Clear filters to see all questions.</span>
          </div>
        )}
      </div>
    </div>
  )
}

function Key({ label, value }: { label: string; value: string }) {
  return (
    <div className="key">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  )
}

function Drawer({
  title,
  close,
  children,
}: {
  title: string
  close: () => void
  children: ReactNode
}) {
  return (
    <div className="drawer-overlay" onClick={close}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <span>Evidence source</span>
            <h2>{title}</h2>
          </div>
          <button className="icon-btn" type="button" onClick={close} aria-label="Close">
            <X />
          </button>
        </div>
        {children}
      </aside>
    </div>
  )
}

function Detail({ go, addAction }: { go: (s: Screen) => void; addAction: () => void }) {
  const [source, setSource] = useState(false)
  const [status, setStatus] = useState('UNREVIEWED')
  const [tab, setTab] = useState('evidence')

  return (
    <div className="detail-page">
      <button className="back" type="button" onClick={() => go('questions')}>
        <ArrowLeft />
        Back to questionnaire
      </button>
      <PageTitle
        eyebrow="Q-E-01 · Environmental · Energy"
        title="Report annual electricity consumption."
        desc="Required customer question · SEDG Energy"
        actions={
          <>
            <StatusPill value="PARTIAL" />
            <StatusPill value={status} />
          </>
        }
      />
      <div className="detail-grid">
        <main className="answer-panel">
          <div className="answer-head">
            <div>
              <Sparkles />
              <b>Suggested answer</b>
              <Pill>AI-assisted draft</Pill>
            </div>
            <button className="link" type="button">
              Edit answer
            </button>
          </div>
          <div className="answer-text">
            38,420 kWh is evidenced for January to March 2025.
            <button type="button" onClick={() => setSource(true)}>
              [1]
            </button>
          </div>
          <div className="callout warning">
            <AlertTriangle />
            <div>
              <b>Coverage is incomplete</b>
              <p>Only 3 of the required 12 months are supported. Electricity bills for April to December 2025 are missing.</p>
            </div>
          </div>
          <div className="priority-box">
            <div>
              <span>Priority</span>
              <strong>82 / 100</strong>
            </div>
            <div>
              <Key label="Required" value="Yes · +35" />
              <Key label="Evidence risk" value="Partial · +25" />
              <Key label="Deadline" value="13 days · +22" />
            </div>
          </div>
          <div className="answer-actions">
            <button className="danger" type="button" onClick={() => setStatus('REJECTED')}>
              <X />
              Reject
            </button>
            <button className="secondary" type="button">
              Not applicable
            </button>
            <button className="primary" type="button" onClick={() => setStatus('CONFIRMED')}>
              <Check />
              Confirm answer
            </button>
          </div>
          <div className="human-note">
            <ShieldCheck />
            Only a human confirmation marks an answer ready. Evidence status remains separate.
          </div>
        </main>
        <aside className="evidence-panel">
          <div className="tabs">
            <button type="button" className={tab === 'evidence' ? 'active' : ''} onClick={() => setTab('evidence')}>
              Evidence (3)
            </button>
            <button type="button" className={tab === 'gap' ? 'active' : ''} onClick={() => setTab('gap')}>
              Gap & action
            </button>
          </div>
          {tab === 'evidence' ? (
            <>
              <div className="source-card selected">
                <div className="source-top">
                  <span>[1]</span>
                  <div>
                    <b>tnb-bills-jan-mar-2025.pdf</b>
                    <small>Page 2 · January 2025</small>
                  </div>
                  <Pill tone="supported">Candidate</Pill>
                </div>
                <blockquote>“Total consumption: 12,840 kWh”</blockquote>
                <button className="link" type="button" onClick={() => setSource(true)}>
                  Open source
                  <ArrowRight />
                </button>
              </div>
              {(
                [
                  ['[2]', 'Page 4 · February 2025', '12,610 kWh'],
                  ['[3]', 'Page 6 · March 2025', '12,970 kWh'],
                ] as const
              ).map(([ref, loc, kwh]) => (
                <div className="source-card" key={ref}>
                  <div className="source-top">
                    <span>{ref}</span>
                    <div>
                      <b>tnb-bills-jan-mar-2025.pdf</b>
                      <small>{loc}</small>
                    </div>
                  </div>
                  <blockquote>“Total consumption: {kwh}”</blockquote>
                </div>
              ))}
            </>
          ) : (
            <div className="gap-card">
              <AlertTriangle />
              <h3>9 months missing</h3>
              <p>Ask Finance to retrieve the remaining electricity bills for April to December 2025.</p>
              <Key label="Suggested owner" value="Finance Manager" />
              <Key label="Recommended due" value="29 Aug 2026" />
              <button
                className="primary full"
                type="button"
                onClick={() => {
                  addAction()
                  go('actions')
                }}
              >
                <Plus />
                Create submission action
              </button>
            </div>
          )}
        </aside>
      </div>
      {source && (
        <Drawer title="tnb-bills-jan-mar-2025.pdf" close={() => setSource(false)}>
          <div className="pdf-preview">
            <div className="pdf-sheet">
              <small>Tenaga Nasional Berhad · Demo</small>
              <h3>Electricity bill</h3>
              <p>Billing period: 01 Jan – 31 Jan 2025</p>
              <div className="highlight">
                <span>Total consumption</span>
                <strong>12,840 kWh</strong>
              </div>
              <p>Premise: Selangor manufacturing site</p>
            </div>
          </div>
          <Key label="Source location" value="Page 2 · Paragraph 6" />
          <Key label="Extraction" value="Parsed text" />
          <Key label="Claim supported" value="Electricity consumed in January 2025" />
          <div className="callout info">
            <CircleHelp />
            <div>
              <b>Candidate link</b>
              <p>Review this evidence before confirming the answer.</p>
            </div>
          </div>
        </Drawer>
      )}
    </div>
  )
}

function Actions({ hasAction }: { hasAction: boolean }) {
  const [create, setCreate] = useState(false)
  const [drawer, setDrawer] = useState(false)

  return (
    <div>
      <PageTitle
        eyebrow="Follow-up work"
        title="Actions"
        desc="Turn response gaps into owned next steps and closure evidence."
        actions={
          <button className="primary" type="button" onClick={() => setCreate(true)}>
            <Plus />
            New action
          </button>
        }
      />
      <div className="tabs page-tabs">
        <button className="active" type="button">
          Submission actions
          <b>{hasAction ? 5 : 4}</b>
        </button>
        <button type="button">
          Improvement actions
          <b>3</b>
        </button>
      </div>
      <div className="toolbar">
        <SearchField placeholder="Search actions" grow />
        <button className="control" type="button">
          All owners
          <ChevronDown />
        </button>
        <button className="control" type="button">
          All status
          <ChevronDown />
        </button>
      </div>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Action</th>
              <th>Linked item</th>
              <th>Owner</th>
              <th>Due</th>
              <th>Status</th>
              <th>Closure evidence</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {hasAction && (
              <tr className="clickable fresh" onClick={() => setDrawer(true)}>
                <td>
                  <b>Collect missing electricity bills</b>
                  <small>Retrieve April–December 2025 bills</small>
                </td>
                <td>
                  <Pill>Q-E-01</Pill>
                </td>
                <td>Finance Manager</td>
                <td>
                  <b>29 Aug 2026</b>
                  <small>7 days left</small>
                </td>
                <td>
                  <Pill tone="warning">Open</Pill>
                </td>
                <td>Not attached</td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            )}
            <tr>
              <td>
                <b>Verify waste recycling rate</b>
                <small>Resolve source discrepancy with Operations</small>
              </td>
              <td>
                <Pill>Q-E-02</Pill>
              </td>
              <td>Operations Manager</td>
              <td>27 Aug 2026</td>
              <td>
                <Pill tone="conflict">Blocked</Pill>
              </td>
              <td>Waiting for weighbridge report</td>
              <td>
                <ArrowRight />
              </td>
            </tr>
            <tr>
              <td>
                <b>Upload current grievance policy</b>
                <small>Replace outdated 2023 policy</small>
              </td>
              <td>
                <Pill>Q-S-02</Pill>
              </td>
              <td>HR Manager</td>
              <td>30 Aug 2026</td>
              <td>
                <Pill tone="partial">In progress</Pill>
              </td>
              <td>Draft attached</td>
              <td>
                <ArrowRight />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      {(create || drawer) && (
        <Drawer
          title={drawer ? 'Collect missing electricity bills' : 'Create submission action'}
          close={() => {
            setCreate(false)
            setDrawer(false)
          }}
        >
          <label>
            Action title
            <input defaultValue="Collect missing electricity bills" />
          </label>
          <label>
            Next step
            <textarea defaultValue="Ask Finance to retrieve electricity bills for April to December 2025." />
          </label>
          <label>
            Owner
            <select defaultValue="Finance Manager">
              <option>Finance Manager</option>
              <option>Operations Manager</option>
            </select>
          </label>
          <label>
            Due date
            <input type="date" defaultValue="2026-08-29" />
          </label>
          <Key label="Linked question" value="Q-E-01 · Annual electricity consumption" />
          <button
            className="primary full"
            type="button"
            onClick={() => {
              setCreate(false)
              setDrawer(false)
            }}
          >
            {drawer ? 'Save changes' : 'Create action'}
          </button>
        </Drawer>
      )}
    </div>
  )
}

function ExportScreen() {
  const [generated, setGenerated] = useState(false)

  return (
    <div>
      <PageTitle
        eyebrow="Customer outputs"
        title="Review & export"
        desc="Generate honest outputs that preserve gaps, assumptions and source traceability."
        actions={
          generated ? (
            <button className="primary" type="button">
              <Download />
              Download package
            </button>
          ) : undefined
        }
      />
      <div className="export-banner">
        <div>
          <AlertTriangle />
          <div>
            <b>5 required answers are not confirmed</b>
            <p>You can generate a marked-up draft, but it will disclose unresolved items and cannot be treated as submission-ready.</p>
          </div>
        </div>
        <button className="secondary" type="button">
          Review blockers
        </button>
      </div>
      <div className="blocker-grid">
        <div>
          <strong>2</strong>
          <span>Missing evidence</span>
          <small>Required questions</small>
        </div>
        <div>
          <strong>1</strong>
          <span>Source conflict</span>
          <small>Human decision needed</small>
        </div>
        <div>
          <strong>2</strong>
          <span>Unconfirmed drafts</span>
          <small>Human review needed</small>
        </div>
        <div>
          <strong>4</strong>
          <span>Open actions</span>
          <small>Before customer due date</small>
        </div>
      </div>
      <div className="export-grid">
        <section className="panel">
          <h2>Output package</h2>
          <p>Choose files to generate for internal review.</p>
          {(
            [
              ['Customer response summary', 'PDF', 'Answers, citations and disclosed gaps'],
              ['Evidence index', 'XLSX', 'Question-to-source traceability'],
              ['Action register', 'CSV', 'Owners, deadlines and closure evidence'],
            ] as const
          ).map(([name, kind, desc]) => (
            <label className="output" key={name}>
              <input type="checkbox" defaultChecked />
              <span className="file-icon">
                <FileCheck2 />
              </span>
              <div>
                <b>{name}</b>
                <small>{desc}</small>
              </div>
              <Pill>{kind}</Pill>
            </label>
          ))}
          <button className="primary full" type="button" onClick={() => setGenerated(true)}>
            <Zap />
            {generated ? 'Regenerate marked-up draft' : 'Generate marked-up draft'}
          </button>
          <div className="human-note">
            <ShieldCheck />
            Generation does not submit anything to the customer.
          </div>
        </section>
        <section className="preview">
          <div className="preview-bar">
            <span>Customer response summary.pdf</span>
            <Pill tone="warning">{generated ? 'Ready · Not submitted' : 'Preview'}</Pill>
          </div>
          <div className="paper">
            <div className="watermark">Draft · Unconfirmed</div>
            <Mark />
            <h2>ESG Questionnaire Response</h2>
            <p>BuktiPack Manufacturing Sdn. Bhd.</p>
            <div className="paper-rule" />
            <h3>Environmental · Energy</h3>
            <b>Annual electricity consumption</b>
            <p>
              38,420 kWh is evidenced for January to March 2025. <sup>[1]</sup>
            </p>
            <div className="paper-warning">
              <AlertTriangle />
              Coverage gap: April–December 2025 bills are missing.
            </div>
            <small>Evidence: tnb-bills-jan-mar-2025.pdf · Pages 2, 4, 6</small>
          </div>
        </section>
      </div>
      {generated && (
        <div className="history">
          <Check />
          <div>
            <b>Draft package generated</b>
            <span>3 files · Generated just now by Nur Aina</span>
          </div>
          <button className="secondary" type="button">
            <Download />
            Download
          </button>
        </div>
      )}
    </div>
  )
}

export default function BuktiApp() {
  const [screen, setScreen] = useState<Screen>('cases')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [hasAction, setHasAction] = useState(false)
  const go = (s: Screen) => {
    setScreen(s)
    setMobileOpen(false)
  }

  return (
    <div className="app-shell">
      {mobileOpen && <div className="nav-scrim" onClick={() => setMobileOpen(false)} />}
      <Sidebar
        screen={screen}
        setScreen={go}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        open={mobileOpen}
      />
      <div className="app-main">
        <Header onMenu={() => setMobileOpen(!mobileOpen)} />
        <main className="content">
          {screen === 'cases' && <Cases go={go} />}
          {screen === 'create' && <CreateCase go={go} />}
          {screen === 'intake' && <Intake />}
          {screen === 'overview' && <Overview go={go} />}
          {screen === 'questions' && <Questions go={go} />}
          {screen === 'detail' && <Detail go={go} addAction={() => setHasAction(true)} />}
          {screen === 'actions' && <Actions hasAction={hasAction} />}
          {screen === 'export' && <ExportScreen />}
        </main>
      </div>
    </div>
  )
}
