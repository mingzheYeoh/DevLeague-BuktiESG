'use client'

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react'
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
type Pillar = 'Environmental' | 'Social' | 'Governance'

type EvidenceSource = {
  ref: string
  doc: string
  location: string
  quote: string
}

type PriorityFactor = {
  label: string
  value: string
}

type QuestionGap = {
  title: string
  description: string
  suggestedOwner: string
  recommendedDue: string
}

type Question = {
  id: string
  q: string
  topic: string
  pillar: Pillar
  required: boolean
  evidence: Status
  review: string
  priority: number
  reason: string
  answer: string
  sources: EvidenceSource[]
  gap: QuestionGap | null
  priorityFactors: PriorityFactor[]
}

const seedQuestions: Question[] = [
  {
    id: 'Q-E-01',
    q: 'Report annual electricity consumption.',
    topic: 'Energy',
    pillar: 'Environmental',
    required: true,
    evidence: 'PARTIAL',
    review: 'UNREVIEWED',
    priority: 82,
    reason: 'Only 3 of 12 months are supported',
    answer: '38,420 kWh is evidenced for January to March 2025.',
    sources: [
      { ref: '[1]', doc: 'tnb-bills-jan-mar-2025.pdf', location: 'Page 2 · January 2025', quote: 'Total consumption: 12,840 kWh' },
      { ref: '[2]', doc: 'tnb-bills-jan-mar-2025.pdf', location: 'Page 4 · February 2025', quote: 'Total consumption: 12,610 kWh' },
      { ref: '[3]', doc: 'tnb-bills-jan-mar-2025.pdf', location: 'Page 6 · March 2025', quote: 'Total consumption: 12,970 kWh' },
    ],
    gap: {
      title: '9 months missing',
      description: 'Ask Finance to retrieve the remaining electricity bills for April to December 2025.',
      suggestedOwner: 'Finance Manager',
      recommendedDue: '29 Aug 2026',
    },
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Partial · +25' },
      { label: 'Deadline', value: '13 days · +22' },
    ],
  },
  {
    id: 'Q-E-02',
    q: 'What percentage of waste was recycled?',
    topic: 'Waste',
    pillar: 'Environmental',
    required: true,
    evidence: 'CONFLICT',
    review: 'NEEDS REVIEW',
    priority: 78,
    reason: 'Two sources report different recycling rates',
    answer: 'Two internal sources report different FY2025 recycling rates: 41% and 53%.',
    sources: [
      { ref: '[1]', doc: 'waste-tracker-2025.xlsx', location: "Sheet 'Summary' · Row 12", quote: 'Recycling rate: 41%' },
      { ref: '[2]', doc: 'weighbridge-report-q4.pdf', location: 'Page 1 · Total', quote: 'Recycling rate: 53%' },
    ],
    gap: {
      title: 'Conflicting figures',
      description: 'Confirm which source reflects the verified weighbridge total and correct the tracker.',
      suggestedOwner: 'Operations Manager',
      recommendedDue: '27 Aug 2026',
    },
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Conflict · +30' },
      { label: 'Deadline', value: '11 days · +13' },
    ],
  },
  {
    id: 'Q-E-03',
    q: 'Describe your environmental policy.',
    topic: 'Policy',
    pillar: 'Environmental',
    required: true,
    evidence: 'SUPPORTED',
    review: 'CONFIRMED',
    priority: 28,
    reason: 'Current signed policy found',
    answer: 'The current signed environmental policy (v3, effective Jan 2025) covers energy, waste and water commitments.',
    sources: [
      { ref: '[1]', doc: 'environmental-policy-v3.pdf', location: 'Page 1 · Policy statement', quote: 'This policy is approved by the Board and reviewed annually.' },
    ],
    gap: null,
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Supported · +5' },
      { label: 'Deadline', value: '13 days · +2' },
    ],
  },
  {
    id: 'Q-S-01',
    q: 'Report workforce injury frequency.',
    topic: 'Health & safety',
    pillar: 'Social',
    required: true,
    evidence: 'MISSING',
    review: 'UNREVIEWED',
    priority: 75,
    reason: 'Incident register not uploaded',
    answer: 'No answer drafted yet. Evidence has not been provided.',
    sources: [],
    gap: {
      title: 'Incident register not uploaded',
      description: 'Request the FY2025 incident register from HR/Safety to calculate the injury frequency rate.',
      suggestedOwner: 'HR Manager',
      recommendedDue: '30 Aug 2026',
    },
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Missing · +30' },
      { label: 'Deadline', value: '8 days · +10' },
    ],
  },
  {
    id: 'Q-S-02',
    q: 'Describe employee grievance channels.',
    topic: 'People',
    pillar: 'Social',
    required: false,
    evidence: 'OUTDATED',
    review: 'NEEDS REVIEW',
    priority: 67,
    reason: 'Policy review date passed',
    answer: 'Grievance channels described per the 2023 employee handbook: hotline, HR escalation, anonymous suggestion box.',
    sources: [
      { ref: '[1]', doc: 'employee-handbook-2023.docx', location: 'Page 14 · Grievance procedure', quote: 'Employees may raise concerns via the confidential hotline or HR.' },
    ],
    gap: {
      title: 'Policy review date passed',
      description: 'Confirm whether the grievance procedure has changed since 2023 and upload the current handbook.',
      suggestedOwner: 'HR Manager',
      recommendedDue: '30 Aug 2026',
    },
    priorityFactors: [
      { label: 'Required', value: 'No · +0' },
      { label: 'Evidence risk', value: 'Outdated · +20' },
      { label: 'Deadline', value: '8 days · +10' },
    ],
  },
  {
    id: 'Q-G-01',
    q: 'Who oversees ESG responsibilities?',
    topic: 'Governance',
    pillar: 'Governance',
    required: true,
    evidence: 'SUPPORTED',
    review: 'CONFIRMED',
    priority: 31,
    reason: 'Board charter and minutes align',
    answer: 'The Board Sustainability Committee oversees ESG responsibilities, chaired by the CFO.',
    sources: [
      { ref: '[1]', doc: 'board-charter-2025.pdf', location: 'Page 3 · Committee mandate', quote: 'The Sustainability Committee is responsible for overseeing ESG matters.' },
    ],
    gap: null,
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Supported · +5' },
      { label: 'Deadline', value: '16 days · +2' },
    ],
  },
  {
    id: 'Q-G-02',
    q: 'Describe anti-bribery controls.',
    topic: 'Ethics',
    pillar: 'Governance',
    required: true,
    evidence: 'UNSUPPORTED',
    review: 'UNREVIEWED',
    priority: 62,
    reason: 'Draft has no linked evidence',
    answer: 'A draft anti-bribery policy has been prepared but is not yet linked to supporting evidence.',
    sources: [],
    gap: {
      title: 'Draft has no linked evidence',
      description: 'Attach the signed anti-bribery policy and any related training records.',
      suggestedOwner: 'Compliance Officer',
      recommendedDue: '5 Sep 2026',
    },
    priorityFactors: [
      { label: 'Required', value: 'Yes · +35' },
      { label: 'Evidence risk', value: 'Unsupported · +25' },
      { label: 'Deadline', value: '14 days · +2' },
    ],
  },
  {
    id: 'Q-G-03',
    q: 'Report whistleblowing cases.',
    topic: 'Ethics',
    pillar: 'Governance',
    required: false,
    evidence: 'SUPPORTED',
    review: 'UNREVIEWED',
    priority: 42,
    reason: 'Register supports zero cases',
    answer: 'The whistleblowing register shows zero reported cases for FY2025.',
    sources: [
      { ref: '[1]', doc: 'whistleblowing-register-2025.pdf', location: 'Page 1 · Register summary', quote: 'No cases recorded in FY2025.' },
    ],
    gap: null,
    priorityFactors: [
      { label: 'Required', value: 'No · +0' },
      { label: 'Evidence risk', value: 'Supported · +5' },
      { label: 'Deadline', value: '14 days · +2' },
    ],
  },
]

function questionStats(questions: Question[]) {
  const total = questions.length
  const requiredQuestions = questions.filter((q) => q.required)
  const requiredCount = requiredQuestions.length
  const confirmedRequired = requiredQuestions.filter((q) => q.review === 'CONFIRMED').length
  const unconfirmedDrafts = questions.filter((q) => q.review !== 'CONFIRMED').length
  const evidenceGaps = questions.filter((q) => ['MISSING', 'PARTIAL', 'UNSUPPORTED'].includes(q.evidence)).length
  const sourceConflicts = questions.filter((q) => q.evidence === 'CONFLICT').length
  const coverage = {
    supported: questions.filter((q) => q.evidence === 'SUPPORTED').length,
    partial: questions.filter((q) => q.evidence === 'PARTIAL').length,
    missing: questions.filter((q) => q.evidence === 'MISSING').length,
    conflict: questions.filter((q) => q.evidence === 'CONFLICT').length,
  }
  const readiness = requiredCount === 0 ? 0 : Math.round((confirmedRequired / requiredCount) * 100)
  return { total, requiredCount, confirmedRequired, unconfirmedDrafts, evidenceGaps, sourceConflicts, coverage, readiness }
}

function pillarReadiness(questions: Question[], pillar: Pillar) {
  const inPillar = questions.filter((q) => q.pillar === pillar)
  const confirmed = inPillar.filter((q) => q.review === 'CONFIRMED').length
  const value = inPillar.length === 0 ? 0 : Math.round((confirmed / inPillar.length) * 100)
  return { value, confirmed, total: inPillar.length }
}

function priorityFactorValue(value: string) {
  const match = value.match(/\+(\d+)/)
  return match ? Number(match[1]) : 0
}

function priorityBreakdownFor(question: Question) {
  return question.priorityFactors.map((factor, i) => ({
    label: factor.label,
    value: priorityFactorValue(factor.value),
    color: `var(--chart-${(i % 5) + 1})`,
  }))
}

const ORG_PROFILE = {
  name: 'BuktiPack Manufacturing Sdn. Bhd.',
  shortName: 'BuktiPack Manufacturing',
  location: 'Selangor',
  employees: 45,
  site: 'Selangor manufacturing site',
}

function docCoverageLabel(doc: string, questions: Question[]) {
  const count = questions.reduce((total, q) => total + q.sources.filter((s) => s.doc === doc).length, 0)
  return count === 0 ? 'No linked questions' : `${count} question${count === 1 ? '' : 's'}`
}

function seedDocs(questions: Question[]): [string, string, string, string][] {
  return [
    ['tnb-bills-jan-mar-2025.pdf', 'Utility bill', 'READY', docCoverageLabel('tnb-bills-jan-mar-2025.pdf', questions)],
    ['environmental-policy-v3.pdf', 'Policy', 'READY', docCoverageLabel('environmental-policy-v3.pdf', questions)],
    ['waste-tracker-2025.xlsx', 'Spreadsheet', 'REVIEW', 'Conflict found'],
    ['employee-handbook-2023.docx', 'Policy', 'OUTDATED', docCoverageLabel('employee-handbook-2023.docx', questions)],
    ['incident-register-scan.pdf', 'Scanned PDF', 'FAILED', 'Needs manual review'],
  ]
}

type CaseStatus = 'draft' | 'in-progress' | 'in-review' | 'completed'

type CaseRecord = {
  id: string
  title: string
  subtitle: string
  customer: string
  dueDate: string
  owner: string
  status: CaseStatus
}

const caseStatusOptions: { value: CaseStatus; label: string; tone: string }[] = [
  { value: 'draft', label: 'Draft', tone: 'unreviewed' },
  { value: 'in-progress', label: 'In progress', tone: 'warning' },
  { value: 'in-review', label: 'In review', tone: 'partial' },
  { value: 'completed', label: 'Completed', tone: 'confirmed' },
]

function caseStatusMeta(status: CaseStatus) {
  return caseStatusOptions.find((o) => o.value === status) ?? caseStatusOptions[0]
}

function seedCases(questions: Question[]): CaseRecord[] {
  const stats = questionStats(questions)
  return [
    {
      id: 'case-seed-1',
      title: 'Major Customer ESG Questionnaire 2026',
      subtitle: `${stats.total} questions · ${stats.requiredCount} required`,
      customer: 'Demo FMCG Customer',
      dueDate: '2026-09-04',
      owner: 'Nur Aina',
      status: 'in-progress',
    },
    {
      id: 'case-seed-2',
      title: 'Supplier Code Review 2026',
      subtitle: '14 questions · 9 required',
      customer: 'Regional Retail Group',
      dueDate: '2026-09-18',
      owner: 'Farid M.',
      status: 'in-review',
    },
  ]
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

function formatDateLabel(iso: string) {
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function daysLeftLabel(iso: string) {
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  const diff = Math.ceil((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return 'Overdue'
  if (diff === 0) return 'Due today'
  return `${diff} day${diff === 1 ? '' : 's'} left`
}

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

function downloadTextFile(filename: string, content: string, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function toCsvValue(value: string | number) {
  const str = String(value)
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str
}

function questionsToCsv(questions: Question[]) {
  const header = ['ID', 'Question', 'Topic', 'Evidence', 'Review', 'Priority', 'Reason']
  const rows = questions.map((q) => [q.id, q.q, q.topic, q.evidence, q.review, q.priority, q.reason])
  return [header, ...rows].map((row) => row.map(toCsvValue).join(',')).join('\n')
}

type ActionRecord = {
  title: string
  linkedQuestionId: string
  owner: string
  due: string
  status: string
  closureEvidence: string
}

function seedActions(questions: Question[]): ActionRecord[] {
  return questions
    .filter((q) => q.gap)
    .slice(0, 3)
    .map((q, i) => ({
      title:
        i === 0
          ? `Collect missing evidence for ${q.id}`
          : i === 1
            ? `Resolve ${q.reason.toLowerCase()}`
            : `Address ${q.gap!.title.toLowerCase()}`,
      linkedQuestionId: q.id,
      owner: q.gap!.suggestedOwner,
      due: q.gap!.recommendedDue,
      status: i === 0 ? 'Open' : i === 1 ? 'Blocked' : 'In progress',
      closureEvidence: i === 0 ? 'Not attached' : i === 1 ? 'Waiting for weighbridge report' : 'Draft attached',
    }))
}

function actionsToCsv(actions: ActionRecord[]) {
  const header = ['Action', 'Linked item', 'Owner', 'Due', 'Status', 'Closure evidence']
  const rows = actions.map((a) => [a.title, a.linkedQuestionId, a.owner, a.due, a.status, a.closureEvidence])
  return [header, ...rows].map((row) => row.map(toCsvValue).join(',')).join('\n')
}

function responseSummaryText(question: Question, org: string) {
  const primarySource = question.sources[0]
  return [
    'ESG Questionnaire Response (DRAFT - not submission-ready)',
    org,
    '',
    `${question.pillar} · ${question.topic}`,
    question.q,
    `${question.answer}${primarySource ? ` [${question.sources.indexOf(primarySource) + 1}]` : ''}`,
    question.gap ? `Coverage gap: ${question.gap.description}` : '',
    primarySource ? `Evidence: ${primarySource.doc}` : '',
    '',
    'This draft discloses unresolved items and must not be treated as submission-ready.',
  ]
    .filter(Boolean)
    .join('\n')
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

function seedEvidenceItems(questions: Question[]): EvidenceItem[] {
  return seedDocs(questions).map(([name, type, status, coverage]) => ({
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

function StatusDropdown({
  value,
  onChange,
}: {
  value: CaseStatus
  onChange: (status: CaseStatus) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement | null>(null)
  const current = caseStatusMeta(value)

  useEffect(() => {
    if (!open) return
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  return (
    <div className="status-dropdown" ref={ref}>
      <button
        type="button"
        className="control status-dropdown-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Pill tone={current.tone}>{current.label}</Pill>
        <ChevronDown />
      </button>
      {open && (
        <ul className="status-dropdown-menu" role="listbox">
          {caseStatusOptions.map((option) => (
            <li key={option.value}>
              <button
                type="button"
                role="option"
                aria-selected={option.value === value}
                className={option.value === value ? 'active' : ''}
                onClick={() => {
                  onChange(option.value)
                  setOpen(false)
                }}
              >
                <Pill tone={option.tone}>{option.label}</Pill>
                {option.value === value && <Check />}
              </button>
            </li>
          ))}
        </ul>
      )}
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

function Header({
  onMenu,
  go,
  caseTitle,
  dueLabel,
  reviewCount,
  ownerName,
}: {
  onMenu: () => void
  go: (s: Screen) => void
  caseTitle: string
  dueLabel: string
  reviewCount: number
  ownerName: string
}) {
  return (
    <>
      <header className="topbar">
        <button className="icon-btn mobile-menu" onClick={onMenu} aria-label="Open navigation" type="button">
          <Menu />
        </button>
        <div className="crumb">
          Cases <span>/</span> {caseTitle}
        </div>
        <div className="top-actions">
          <button className="search" type="button">
            <Search />
            <span>Search evidence</span>
            <kbd>⌘ K</kbd>
          </button>
          <Pill tone="warning">
            <Clock3 />
            {dueLabel}
          </Pill>
          <button className="review-btn" type="button" onClick={() => go('questions')}>
            <ClipboardCheck />
            Review queue
            <b>{reviewCount}</b>
          </button>
          <button className="icon-btn" aria-label="Notifications" type="button">
            <Bell />
          </button>
          <div className="avatar" aria-label={ownerName}>
            {initials(ownerName)}
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
  workflowLabel,
  reviewCount,
}: {
  screen: Screen
  setScreen: (s: Screen) => void
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  open: boolean
  workflowLabel: string
  reviewCount: number
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
      <div className="case-step">{workflowLabel}</div>
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
              aria-label={label === 'Questionnaire' ? `Questionnaire, ${reviewCount} items` : label}
            >
              <Icon />
              <span>{label}</span>
              {label === 'Questionnaire' && <em>{reviewCount}</em>}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace">
          <div className="avatar small">{initials(ORG_PROFILE.shortName)}</div>
          <div>
            <b>{ORG_PROFILE.shortName}</b>
            <small>
              {ORG_PROFILE.location} · {ORG_PROFILE.employees} employees
            </small>
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

function Cases({
  go,
  cases,
  stats,
  openActionCount,
  onSelectCase,
}: {
  go: (s: Screen) => void
  cases: CaseRecord[]
  stats: ReturnType<typeof questionStats>
  openActionCount: number
  onSelectCase: (caseId: string) => void
}) {
  const dueSoon = cases.filter((c) => {
    const diff = Math.ceil((new Date(`${c.dueDate}T00:00:00`).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    return diff >= 0 && diff <= 14
  }).length
  const customerCount = new Set(cases.map((c) => c.customer)).size

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
        <Summary label="Active cases" value={String(cases.length)} sub={`Across ${customerCount} customers`} />
        <Summary label="Due soon" value={String(dueSoon)} sub="Within the next 14 days" tone="warn-text" />
        <Summary
          label="Required confirmed"
          value={`${stats.confirmedRequired} / ${stats.requiredCount}`}
          sub="Across active cases"
        />
        <Summary label="Open actions" value={String(openActionCount)} sub="Awaiting closure evidence" tone="warn-text" />
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
            {cases.map((c) => (
              <tr key={c.id} className="clickable" onClick={() => {
                onSelectCase(c.id)
                go('overview')
              }}>
                <td>
                  <div className="cell-title">
                    <span className="file-icon">
                      <FileSpreadsheet />
                    </span>
                    <div>
                      <b>{c.title}</b>
                      <small>{c.subtitle}</small>
                    </div>
                  </div>
                </td>
                <td>{c.customer}</td>
                <td>
                  <b>—</b>
                  <Meter value={0} />
                  <small>Not started</small>
                </td>
                <td>
                  <b>{formatDateLabel(c.dueDate)}</b>
                  <small>{daysLeftLabel(c.dueDate)}</small>
                </td>
                <td>
                  <div className="person">
                    <span>{initials(c.owner)}</span>
                    {c.owner}
                  </div>
                </td>
                <td>
                  <Pill tone={caseStatusMeta(c.status).tone}>{caseStatusMeta(c.status).label}</Pill>
                </td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {cases.length === 0 && (
          <div className="empty">
            <FileSpreadsheet />
            <b>No cases yet</b>
            <span>Create a response case to get started.</span>
          </div>
        )}
      </div>
    </div>
  )
}

function CreateCase({ go, onCreate }: { go: (s: Screen) => void; onCreate: (c: CaseRecord) => void }) {
  const [step, setStep] = useState(1)
  const steps = ['Case details', 'Reporting scope', 'Questionnaire', 'Review']

  const [title, setTitle] = useState('Major Customer ESG Questionnaire 2026')
  const [customer, setCustomer] = useState('Demo FMCG Customer')
  const [dueDate, setDueDate] = useState('2026-09-04')
  const [owner, setOwner] = useState('Nur Aina')

  const [questionnaireFile, setQuestionnaireFile] = useState<EvidenceItem | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  function addQuestionnaireFile(fileList: FileList | File[]) {
    const file = Array.from(fileList)[0]
    if (!file) return
    setQuestionnaireFile(fileToEvidenceItem(file))
  }

  function handleCreate() {
    onCreate({
      id: `case-${Date.now()}`,
      title: title.trim() || 'Untitled case',
      subtitle: questionnaireFile ? `${questionnaireFile.name}` : 'No questionnaire uploaded',
      customer: customer.trim() || 'Unnamed customer',
      dueDate,
      owner,
      status: 'draft',
    })
    go('intake')
  }

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
              <input value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <div className="form-grid">
              <label>
                Customer
                <input value={customer} onChange={(e) => setCustomer(e.target.value)} />
              </label>
              <label>
                Due date
                <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              </label>
            </div>
            <label>
              Internal owner
              <select value={owner} onChange={(e) => setOwner(e.target.value)}>
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
            {!questionnaireFile && (
              <div
                className={`dropzone clickable${dragActive ? ' active' : ''}`}
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
                onDrop={(e) => {
                  e.preventDefault()
                  setDragActive(false)
                  if (e.dataTransfer.files?.length) addQuestionnaireFile(e.dataTransfer.files)
                }}
              >
                <UploadCloud />
                <b>Drop customer questionnaire here</b>
                <span>PDF, DOCX, XLSX or CSV · Maximum 25 MB</span>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files?.length) addQuestionnaireFile(e.target.files)
                e.target.value = ''
              }}
            />
            {questionnaireFile && (
              <div className="uploaded">
                <FileKindIcon kind={questionnaireFile.kind} />
                <div>
                  <b>{questionnaireFile.name}</b>
                  <small>{questionnaireFile.size ? formatBytes(questionnaireFile.size) : ''}</small>
                </div>
                <button
                  className="icon-btn"
                  type="button"
                  aria-label="Remove file"
                  onClick={() => setQuestionnaireFile(null)}
                >
                  <X />
                </button>
              </div>
            )}
          </>
        )}
        {step === 4 && (
          <>
            <h2>Review case setup</h2>
            <div className="review-list">
              <Key label="Customer" value={customer || 'Unnamed customer'} />
              <Key label="Case title" value={title || 'Untitled case'} />
              <Key
                label="Questionnaire"
                value={questionnaireFile ? questionnaireFile.name : 'No questionnaire uploaded'}
              />
              <Key label="Due date" value={formatDateLabel(dueDate)} />
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
            <button className="primary" type="button" onClick={handleCreate}>
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

function Intake({ questions }: { questions: Question[] }) {
  const [items, setItems] = useState<EvidenceItem[]>(() => seedEvidenceItems(questions))
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
      {selected && (
        <EvidencePreviewDrawer
          item={selected}
          close={() => setSelectedId(null)}
          onUpdate={(patch) => setItems((prev) => prev.map((i) => (i.id === selected.id ? { ...i, ...patch } : i)))}
        />
      )}
    </div>
  )
}

const FILE_TYPE_OPTIONS: { label: string; kind: FileKind }[] = [
  { label: 'PDF document', kind: 'pdf' },
  { label: 'Image', kind: 'image' },
  { label: 'Spreadsheet', kind: 'spreadsheet' },
  { label: 'Word document', kind: 'doc' },
  { label: 'Document', kind: 'other' },
]

const PROCESSING_STATUS_OPTIONS = ['PROCESSING', 'READY', 'REVIEW', 'OUTDATED', 'FAILED']

const STATUS_TONE_COLORS: Record<string, { bg: string; color: string }> = {
  PROCESSING: { bg: 'var(--info-bg)', color: 'var(--info)' },
  READY: { bg: 'var(--teal-soft)', color: '#15786f' },
  REVIEW: { bg: '#eef1f3', color: '#5c6974' },
  OUTDATED: { bg: '#eef1f3', color: '#5c6974' },
  FAILED: { bg: 'var(--danger-soft)', color: 'var(--danger)' },
}

function EvidencePreviewDrawer({
  item,
  close,
  onUpdate,
}: {
  item: EvidenceItem
  close: () => void
  onUpdate: (patch: Partial<EvidenceItem>) => void
}) {
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
      <div className="evidence-edit-row">
        <label>
          File type
          <select
            value={item.kind}
            onChange={(e) => {
              const kind = e.target.value as FileKind
              const match = FILE_TYPE_OPTIONS.find((opt) => opt.kind === kind)
              onUpdate({ kind, type: match ? match.label : item.type })
            }}
          >
            {FILE_TYPE_OPTIONS.map((opt) => (
              <option key={opt.kind} value={opt.kind}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Processing status
          <select
            className="status-select"
            style={{
              backgroundColor: STATUS_TONE_COLORS[item.status]?.bg,
              color: STATUS_TONE_COLORS[item.status]?.color,
            }}
            value={item.status}
            onChange={(e) => onUpdate({ status: e.target.value })}
          >
            {PROCESSING_STATUS_OPTIONS.map((status) => (
              <option
                key={status}
                value={status}
                style={{
                  backgroundColor: STATUS_TONE_COLORS[status]?.bg,
                  color: STATUS_TONE_COLORS[status]?.color,
                }}
              >
                {formatStatus(status)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </Drawer>
  )
}

function Overview({
  go,
  questions,
  caseTitle,
  dueLabel,
  openActionCount,
  actionsDueThisWeek,
  activity,
}: {
  go: (s: Screen) => void
  questions: Question[]
  caseTitle: string
  dueLabel: string
  openActionCount: number
  actionsDueThisWeek: number
  activity: { initials: string; text: string; time: string }[]
}) {
  const stats = questionStats(questions)
  const pillars: Pillar[] = ['Environmental', 'Social', 'Governance']
  const processingIssues = seedDocs(questions).filter(([, , status]) => status === 'FAILED')

  return (
    <div>
      <PageTitle
        eyebrow={caseTitle}
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
          <div className="ring" style={{ '--p': stats.readiness } as CSSProperties}>
            <div className="ring-inner">
              <strong>{stats.readiness}%</strong>
              <span>ready</span>
            </div>
          </div>
          <div>
            <Pill tone="warning">{dueLabel}</Pill>
            <h2>
              {stats.confirmedRequired} of {stats.requiredCount} required answers confirmed
            </h2>
            <p>
              {stats.requiredCount - stats.confirmedRequired} required answers still need evidence or human review
              before export.
            </p>
            <Meter value={stats.readiness} />
          </div>
        </div>
        <div className="readiness-stats">
          <Summary label="Confirmed" value={String(stats.confirmedRequired)} sub="Required answers" />
          <Summary label="Unconfirmed drafts" value={String(stats.unconfirmedDrafts)} sub="Human review needed" />
          <Summary
            label="Open actions"
            value={String(openActionCount)}
            sub={`${actionsDueThisWeek} due this week`}
          />
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
          {pillars.map((name) => {
            const { value, confirmed } = pillarReadiness(questions, name)
            return (
              <div className="pillar" key={name}>
                <div className="pillar-icon">{name[0]}</div>
                <div>
                  <b>{name}</b>
                  <small>{confirmed} confirmed</small>
                </div>
                <Meter value={value} />
                <strong>{value}%</strong>
              </div>
            )
          })}
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
          {[...questions]
            .sort((a, b) => b.priority - a.priority)
            .slice(0, 4)
            .map((q) => (
              <button key={q.id} type="button" onClick={() => go('detail')}>
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
              <p>Across all {stats.total} questions</p>
            </div>
          </div>
          <div className="coverage">
            <div>
              <span className="supported">{stats.coverage.supported}</span>
              <small>Supported</small>
            </div>
            <div>
              <span className="partial">{stats.coverage.partial}</span>
              <small>Partial</small>
            </div>
            <div>
              <span className="missing">{stats.coverage.missing}</span>
              <small>Missing</small>
            </div>
            <div>
              <span className="conflict">{stats.coverage.conflict}</span>
              <small>Conflict</small>
            </div>
          </div>
          {processingIssues.length > 0 && (
            <div className="callout warning">
              <AlertTriangle />
              <div>
                <b>{processingIssues.length} processing issue{processingIssues.length === 1 ? '' : 's'}</b>
                <p>{processingIssues[0][0]} needs manual review.</p>
              </div>
              <button className="link" type="button" onClick={() => go('intake')}>
                Inspect
              </button>
            </div>
          )}
        </section>
        <section className="panel activity">
          <div className="section-head">
            <div>
              <h2>Recent activity</h2>
              <p>Latest workspace changes</p>
            </div>
          </div>
          {activity.map((entry) => (
            <div key={entry.text}>
              <span>{entry.initials}</span>
              <p>
                <b>{entry.text}</b>
                <small>{entry.time}</small>
              </p>
            </div>
          ))}
        </section>
      </div>
    </div>
  )
}

function Questions({
  go,
  questions,
}: {
  go: (s: Screen, questionId?: string) => void
  questions: Question[]
}) {
  const [filter, setFilter] = useState('All')
  const filters = [
    ['All', 'All'],
    ['PARTIAL', 'Partial'],
    ['MISSING', 'Missing'],
    ['CONFLICT', 'Conflict'],
  ] as const
  const list = filter === 'All' ? questions : questions.filter((q) => q.evidence === filter)
  const stats = questionStats(questions)

  return (
    <div>
      <PageTitle
        eyebrow="Question workbench"
        title="Customer questionnaire"
        desc={`${stats.total} questions · ${stats.requiredCount} required · Separate evidence from human review.`}
        actions={
          <button
            className="secondary"
            type="button"
            onClick={() => downloadTextFile('questionnaire.csv', questionsToCsv(questions), 'text/csv;charset=utf-8')}
          >
            <Download />
            Export list
          </button>
        }
      />
      <div className="summary-strip">
        <b>
          {stats.confirmedRequired} <span>confirmed required</span>
        </b>
        <b>
          {stats.unconfirmedDrafts} <span>unconfirmed drafts</span>
        </b>
        <b>
          {stats.evidenceGaps} <span>open evidence gaps</span>
        </b>
        <b>
          {stats.sourceConflicts} <span>source conflicts</span>
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
              <tr key={q.id} className="clickable" onClick={() => go('detail', q.id)}>
                <td>
                  <div className="question-cell">
                    <span>{q.id}</span>
                    <b>{q.q}</b>
                    <small>{q.required ? 'Required' : 'Optional'}</small>
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

function Detail({
  go,
  question,
  onReview,
  addAction,
}: {
  go: (s: Screen) => void
  question: Question
  onReview: (id: string, review: string) => void
  addAction: () => void
}) {
  const [activeSource, setActiveSource] = useState<EvidenceSource | null>(null)
  const [tab, setTab] = useState('evidence')
  const priorityBreakdown = priorityBreakdownFor(question)

  return (
    <div className="detail-page">
      <button className="back" type="button" onClick={() => go('questions')}>
        <ArrowLeft />
        Back to questionnaire
      </button>
      <PageTitle
        eyebrow={`${question.id} · ${question.pillar} · ${question.topic}`}
        title={question.q}
        desc={`${question.required ? 'Required' : 'Optional'} customer question`}
        actions={
          <>
            <StatusPill value={question.evidence} />
            <StatusPill value={question.review} />
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
            {question.answer}
            {question.sources[0] && (
              <button type="button" onClick={() => setActiveSource(question.sources[0])}>
                {question.sources[0].ref}
              </button>
            )}
          </div>
          {question.gap && (
            <div className="callout warning">
              <AlertTriangle />
              <div>
                <b>{question.gap.title}</b>
                <p>{question.gap.description}</p>
              </div>
            </div>
          )}
          <div className="priority-box">
            <div>
              <span>Priority</span>
              <strong>{question.priority} / 100</strong>
            </div>
            <div className="priority-breakdown-visual">
              {priorityBreakdown.map((item, i) => (
                <div key={i} className="breakdown-item">
                  <div className="breakdown-bar" style={{ width: `${item.value * 1.2}px`, backgroundColor: item.color }} />
                  <small>{item.label}</small>
                </div>
              ))}
            </div>
            <div>
              {question.priorityFactors.map((factor) => (
                <Key key={factor.label} label={factor.label} value={factor.value} />
              ))}
            </div>
          </div>
          <div className="answer-actions">
            <button className="danger" type="button" onClick={() => onReview(question.id, 'REJECTED')}>
              <X />
              Reject
            </button>
            <button className="secondary" type="button">
              Not applicable
            </button>
            <button className="primary" type="button" onClick={() => onReview(question.id, 'CONFIRMED')}>
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
              Evidence ({question.sources.length})
            </button>
            <button type="button" className={tab === 'gap' ? 'active' : ''} onClick={() => setTab('gap')}>
              Gap & action
            </button>
          </div>
          {tab === 'evidence' ? (
            question.sources.length > 0 ? (
              question.sources.map((source, i) => (
                <div className={`source-card${i === 0 ? ' selected' : ''}`} key={source.ref}>
                  <div className="source-top">
                    <span>{source.ref}</span>
                    <div>
                      <b>{source.doc}</b>
                      <small>{source.location}</small>
                    </div>
                    {i === 0 && <Pill tone="supported">Candidate</Pill>}
                  </div>
                  <blockquote>“{source.quote}”</blockquote>
                  {i === 0 && (
                    <button className="link" type="button" onClick={() => setActiveSource(source)}>
                      Open source
                      <ArrowRight />
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div className="gap-card">
                <AlertTriangle />
                <h3>No evidence linked</h3>
                <p>No supporting documents have been linked to this question yet.</p>
              </div>
            )
          ) : question.gap ? (
            <div className="gap-card">
              <AlertTriangle />
              <h3>{question.gap.title}</h3>
              <p>{question.gap.description}</p>
              <Key label="Suggested owner" value={question.gap.suggestedOwner} />
              <Key label="Recommended due" value={question.gap.recommendedDue} />
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
          ) : (
            <div className="gap-card">
              <Check />
              <h3>No gaps</h3>
              <p>This question is fully supported and confirmed.</p>
            </div>
          )}
        </aside>
      </div>
      {activeSource && (
        <Drawer title={activeSource.doc} close={() => setActiveSource(null)}>
          <div className="pdf-preview">
            <div className="pdf-sheet">
              <small>{ORG_PROFILE.name} · Demo</small>
              <h3>{activeSource.doc}</h3>
              <p>{activeSource.location}</p>
              <div className="highlight">
                <span>Extracted text</span>
                <strong>{activeSource.quote}</strong>
              </div>
              <p>Premise: {ORG_PROFILE.site}</p>
            </div>
          </div>
          <Key label="Source location" value={activeSource.location} />
          <Key label="Extraction" value="Parsed text" />
          <Key label="Claim supported" value={question.q} />
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

function actionStatusTone(status: string) {
  const lower = status.toLowerCase()
  if (lower === 'blocked') return 'conflict'
  if (lower === 'in progress') return 'partial'
  return 'warning'
}

function Actions({ actions }: { actions: ActionRecord[] }) {
  const [create, setCreate] = useState(false)
  const [selected, setSelected] = useState<ActionRecord | null>(null)

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
          <b>{actions.length}</b>
        </button>
        <button type="button">
          Improvement actions
          <b>0</b>
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
            {actions.map((a, i) => (
              <tr key={`${a.linkedQuestionId}-${i}`} className="clickable" onClick={() => setSelected(a)}>
                <td>
                  <b>{a.title}</b>
                </td>
                <td>
                  <Pill>{a.linkedQuestionId}</Pill>
                </td>
                <td>{a.owner}</td>
                <td>{a.due}</td>
                <td>
                  <Pill tone={actionStatusTone(a.status)}>{a.status}</Pill>
                </td>
                <td>{a.closureEvidence}</td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {actions.length === 0 && (
          <div className="empty">
            <ClipboardCheck />
            <b>No actions yet</b>
            <span>Create submission actions from question gaps.</span>
          </div>
        )}
      </div>
      {(create || selected) && (
        <Drawer
          title={selected ? selected.title : 'Create submission action'}
          close={() => {
            setCreate(false)
            setSelected(null)
          }}
        >
          <label>
            Action title
            <input defaultValue={selected?.title ?? ''} />
          </label>
          <label>
            Next step
            <textarea defaultValue={selected?.closureEvidence ?? ''} />
          </label>
          <label>
            Owner
            <select defaultValue={selected?.owner ?? ''}>
              <option>Finance Manager</option>
              <option>Operations Manager</option>
              <option>HR Manager</option>
              <option>Compliance Officer</option>
            </select>
          </label>
          <label>
            Due date
            <input type="text" defaultValue={selected?.due ?? ''} />
          </label>
          {selected && <Key label="Linked question" value={selected.linkedQuestionId} />}
          <button
            className="primary full"
            type="button"
            onClick={() => {
              setCreate(false)
              setSelected(null)
            }}
          >
            {selected ? 'Save changes' : 'Create action'}
          </button>
        </Drawer>
      )}
    </div>
  )
}

function ExportScreen({ questions, actions }: { questions: Question[]; actions: ActionRecord[] }) {
  const [generated, setGenerated] = useState(false)
  const [showBlockers, setShowBlockers] = useState(false)
  const stats = questionStats(questions)
  const previewQuestion = questions.find((q) => q.gap) ?? questions[0]
  const previewSource = previewQuestion?.sources[0]

  function downloadPackage() {
    downloadTextFile(
      'customer-response-summary.txt',
      responseSummaryText(previewQuestion, ORG_PROFILE.name)
    )
    downloadTextFile('evidence-index.csv', questionsToCsv(questions), 'text/csv;charset=utf-8')
    downloadTextFile('action-register.csv', actionsToCsv(actions), 'text/csv;charset=utf-8')
  }

  return (
    <div>
      <PageTitle
        eyebrow="Customer outputs"
        title="Review & export"
        desc="Generate honest outputs that preserve gaps, assumptions and source traceability."
        actions={
          generated ? (
            <button className="primary" type="button" onClick={downloadPackage}>
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
            <b>{stats.requiredCount - stats.confirmedRequired} required answers are not confirmed</b>
            <p>You can generate a marked-up draft, but it will disclose unresolved items and cannot be treated as submission-ready.</p>
          </div>
        </div>
        <button className="secondary" type="button" onClick={() => setShowBlockers(true)}>
          Review blockers
        </button>
      </div>
      <div className="blocker-grid">
        <div>
          <strong>{stats.coverage.missing}</strong>
          <span>Missing evidence</span>
          <small>Required questions</small>
        </div>
        <div>
          <strong>{stats.sourceConflicts}</strong>
          <span>Source conflict</span>
          <small>Human decision needed</small>
        </div>
        <div>
          <strong>{stats.unconfirmedDrafts}</strong>
          <span>Unconfirmed drafts</span>
          <small>Human review needed</small>
        </div>
        <div>
          <strong>{actions.length}</strong>
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
            <p>{ORG_PROFILE.name}</p>
            <div className="paper-rule" />
            {previewQuestion && (
              <>
                <h3>
                  {previewQuestion.pillar} · {previewQuestion.topic}
                </h3>
                <b>{previewQuestion.q}</b>
                <p>
                  {previewQuestion.answer} {previewSource && <sup>{previewSource.ref}</sup>}
                </p>
                {previewQuestion.gap && (
                  <div className="paper-warning">
                    <AlertTriangle />
                    Coverage gap: {previewQuestion.gap.description}
                  </div>
                )}
                {previewSource && <small>Evidence: {previewSource.doc}</small>}
              </>
            )}
          </div>
        </section>
      </div>
      {generated && (
        <div className="history">
          <Check />
          <div>
            <b>Draft package generated</b>
            <span>3 files · Generated just now</span>
          </div>
          <button className="secondary" type="button" onClick={downloadPackage}>
            <Download />
            Download
          </button>
        </div>
      )}
      {showBlockers && (
        <Drawer title="Review blockers" close={() => setShowBlockers(false)}>
          <div className="gap-card">
            <AlertTriangle />
            <h3>{stats.requiredCount - stats.confirmedRequired} required answers are not confirmed</h3>
            <p>Resolve these before the package can be treated as submission-ready.</p>
          </div>
          <Key label="Missing evidence" value={`${stats.coverage.missing} required questions`} />
          <Key label="Source conflict" value={`${stats.sourceConflicts} needs a human decision`} />
          <Key label="Unconfirmed drafts" value={`${stats.unconfirmedDrafts} need human review`} />
          <Key label="Open actions" value={`${actions.length} before the customer due date`} />
        </Drawer>
      )}
    </div>
  )
}

export default function BuktiApp() {
  const [screen, setScreen] = useState<Screen>('cases')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [questions, setQuestions] = useState<Question[]>(seedQuestions)
  const [activeQuestionId, setActiveQuestionId] = useState<string>(seedQuestions[0].id)
  const [cases, setCases] = useState<CaseRecord[]>(() => seedCases(seedQuestions))
  const [selectedCaseId, setSelectedCaseId] = useState<string>(() => seedCases(seedQuestions)[0]?.id ?? '')
  const [extraActions, setExtraActions] = useState<ActionRecord[]>([])
  const [activityLog, setActivityLog] = useState<{ initials: string; text: string; time: string }[]>([
    { initials: 'NA', text: 'Nur Aina confirmed Q-G-01', time: '18 min ago' },
    { initials: 'FM', text: 'Finance Manager uploaded utility bills', time: '42 min ago' },
    { initials: 'BK', text: 'BuktiESG found a source conflict', time: '1 hr ago' },
  ])

  const selectedCase = cases.find((c) => c.id === selectedCaseId)

  const addActivity = (text: string, initials = 'BK') => {
    setActivityLog((prev) => [{ initials, text, time: 'Just now' }, ...prev.slice(0, 9)])
  }

  const go = (s: Screen, questionId?: string) => {
    if (questionId) setActiveQuestionId(questionId)
    if (s === 'overview' && !selectedCaseId && cases.length > 0) {
      setSelectedCaseId(cases[0].id)
    }
    setScreen(s)
    setMobileOpen(false)
  }
  const addCase = (c: CaseRecord) => {
    setCases((prev) => [c, ...prev])
    setSelectedCaseId(c.id)
    addActivity(`Case created: ${c.title}`, 'BK')
  }
  const onReview = (id: string, review: string) => {
    const question = questions.find((q) => q.id === id)
    setQuestions((prev) => prev.map((q) => (q.id === id ? { ...q, review } : q)))
    if (review === 'CONFIRMED' && question) {
      addActivity(`Nur Aina confirmed ${question.id}`, 'NA')
    } else if (review === 'REJECTED' && question) {
      addActivity(`Nur Aina rejected ${question.id}`, 'NA')
    }
  }

  const stats = questionStats(questions)
  const baseActions = seedActions(questions)
  const allActions = [...extraActions, ...baseActions]
  const activeQuestion = questions.find((q) => q.id === activeQuestionId) ?? questions[0]
  const currentCaseDueDate = selectedCase?.dueDate ?? '2026-09-04'
  const dueLabel = `${daysLeftLabel(currentCaseDueDate) || 'Due today'}`
  const actionsDueThisWeek = allActions.filter((a) => {
    const diff = Math.ceil((new Date(`${a.due}T00:00:00`).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    return diff >= 0 && diff <= 7
  }).length

  function addFollowUpAction() {
    if (!activeQuestion.gap) return
    setExtraActions((prev) => [
      {
        title: `Collect missing evidence for ${activeQuestion.id}`,
        linkedQuestionId: activeQuestion.id,
        owner: activeQuestion.gap!.suggestedOwner,
        due: activeQuestion.gap!.recommendedDue,
        status: 'Open',
        closureEvidence: 'Not attached',
      },
      ...prev,
    ])
    addActivity(`Action created for ${activeQuestion.id}`, 'NA')
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
        workflowLabel={`Response workflow · ${dueLabel}`}
        reviewCount={stats.unconfirmedDrafts}
      />
      <div className="app-main">
        <Header
          onMenu={() => setMobileOpen(!mobileOpen)}
          go={go}
          caseTitle={selectedCase?.title ?? 'Response case'}
          dueLabel={dueLabel}
          reviewCount={stats.unconfirmedDrafts}
          ownerName={selectedCase?.owner ?? 'Nur Aina'}
        />
        <main className="content">
          {screen === 'cases' && (
            <Cases go={go} cases={cases} stats={stats} openActionCount={allActions.length} onSelectCase={setSelectedCaseId} />
          )}
          {screen === 'create' && <CreateCase go={go} onCreate={addCase} />}
          {screen === 'intake' && <Intake questions={questions} />}
          {screen === 'overview' && (
            <Overview
              go={go}
              questions={questions}
              caseTitle={selectedCase?.title ?? 'Response case'}
              dueLabel={dueLabel}
              openActionCount={allActions.length}
              actionsDueThisWeek={actionsDueThisWeek}
              activity={activityLog}
            />
          )}
          {screen === 'questions' && <Questions go={go} questions={questions} />}
          {screen === 'detail' && (
            <Detail go={go} question={activeQuestion} onReview={onReview} addAction={addFollowUpAction} />
          )}
          {screen === 'actions' && <Actions actions={allActions} />}
          {screen === 'export' && <ExportScreen questions={questions} actions={allActions} />}
        </main>
      </div>
    </div>
  )
}
