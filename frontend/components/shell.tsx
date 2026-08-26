'use client'

/** Application shell: sidebar navigation and the top bar. */
import {
  Bell,
  BookOpen,
  BriefcaseBusiness,
  ClipboardCheck,
  Clock3,
  Download,
  FolderOpen,
  LayoutDashboard,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Sparkles,
  WifiOff,
} from 'lucide-react'

import { initials } from '@/lib/format'

import { Mark, Pill } from './primitives'

export type Screen =
  | 'cases'
  | 'create'
  | 'intake'
  | 'overview'
  | 'questions'
  | 'detail'
  | 'actions'
  | 'export'

const NAV = [
  ['cases', 'Cases', BriefcaseBusiness],
  ['overview', 'Overview', LayoutDashboard],
  ['questions', 'Questionnaire', BookOpen],
  ['intake', 'Evidence', FolderOpen],
  ['actions', 'Actions', ClipboardCheck],
  ['export', 'Export', Download],
] as const

export function Sidebar({
  screen,
  setScreen,
  collapsed,
  setCollapsed,
  open,
  workflowLabel,
  reviewCount,
  workspaceName,
  workspaceSub,
}: {
  screen: Screen
  setScreen: (s: Screen) => void
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  open: boolean
  workflowLabel: string
  reviewCount: number
  workspaceName: string
  workspaceSub: string
}) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${open ? 'open' : ''}`}>
      <div className="brand">
        <Mark />
        <div>
          {/* Split so "ESG" can carry the logo's green, as the lockup does.
              Still one word to a screen reader and to text selection. */}
          <strong>
            Bukti<span>ESG</span>
          </strong>
          <small>Evidence operations</small>
        </div>
      </div>
      <div className="case-step">{workflowLabel}</div>
      <nav>
        {NAV.map(([id, label, Icon]) => {
          const active = screen === id || (screen === 'detail' && id === 'questions')
          return (
            <button
              key={id}
              type="button"
              className={active ? 'active' : ''}
              onClick={() => setScreen(id)}
              title={label}
              aria-current={active ? 'page' : undefined}
              aria-label={
                label === 'Questionnaire'
                  ? `Questionnaire, ${reviewCount} answers awaiting review`
                  : label
              }
            >
              <Icon />
              <span>{label}</span>
              {label === 'Questionnaire' && reviewCount > 0 && <em>{reviewCount}</em>}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace">
          <div className="avatar small">{initials(workspaceName)}</div>
          <div>
            <b>{workspaceName}</b>
            <small>{workspaceSub}</small>
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

export function Header({
  onMenu,
  onOpenReviewQueue,
  caseTitle,
  dueLabel,
  reviewCount,
  accountEmail,
  onOpenAccount,
  apiOnline,
}: {
  onMenu: () => void
  onOpenReviewQueue: () => void
  caseTitle: string
  dueLabel: string
  reviewCount: number
  accountEmail: string
  onOpenAccount: () => void
  apiOnline: boolean | null
}) {
  return (
    <>
      <header className="topbar">
        <button
          className="icon-btn mobile-menu"
          onClick={onMenu}
          aria-label="Open navigation"
          type="button"
        >
          <Menu />
        </button>
        <div className="crumb">
          Cases <span>/</span> {caseTitle}
        </div>
        <div className="top-actions">
          <button className="search" type="button" disabled title="Search is not implemented yet">
            <Search />
            <span>Search evidence</span>
            <kbd>⌘ K</kbd>
          </button>
          <Pill tone="warning">
            <Clock3 />
            {dueLabel}
          </Pill>
          <button className="review-btn" type="button" onClick={onOpenReviewQueue}>
            <ClipboardCheck />
            Review queue
            <b>{reviewCount}</b>
          </button>
          <button className="icon-btn" aria-label="Notifications" type="button" disabled>
            <Bell />
          </button>
          <button
            className="avatar"
            type="button"
            data-testid="account-button"
            onClick={onOpenAccount}
            aria-label={`Signed in as ${accountEmail}. Open account menu.`}
            title={`Signed in as ${accountEmail}`}
          >
            {initials(accountEmail)}
          </button>
        </div>
      </header>
      {apiOnline === false && (
        <div className="prototype offline" role="alert">
          <WifiOff />
          Backend unreachable · start the API (<code>uv run uvicorn app.main:app --reload</code> in{' '}
          <code>backend/</code>) · nothing on screen is sample data, so screens stay empty until it
          responds
        </div>
      )}
      <div className="prototype">
        <Sparkles />
        Prototype workspace · Synthetic, de-identified data only · Not an audit or certification
      </div>
    </>
  )
}
