'use client'

/**
 * The sign-in fields.
 *
 * One component, used by both `AuthScreen` and `ReauthOverlay`. Written that
 * way on purpose: validation, the error copy and the password hint duplicated
 * across two surfaces is the defect this repository keeps producing — the same
 * statement in two places, corrected in one.
 */
import { useState } from 'react'

import { errorMessage } from '@/lib/api'
import { useSession } from '@/lib/session'

import { ErrorNotice } from '../primitives'

export function SignInForm({
  onDone,
  submitLabel = 'Sign in',
  initialEmail = '',
}: {
  onDone?: () => void
  submitLabel?: string
  initialEmail?: string
}) {
  const { signIn } = useSession()
  const [email, setEmail] = useState(initialEmail)
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setError(null)
    setBusy(true)
    try {
      await signIn({ email: email.trim(), password })
      onDone?.()
    } catch (err) {
      // The server answers 401 identically for a wrong password and an
      // address that does not exist. Do not add copy that guesses which.
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      className="auth-form"
      data-testid="sign-in-form"
      onSubmit={(e) => {
        e.preventDefault()
        void submit()
      }}
    >
      {error ? <ErrorNotice message={error} /> : null}
      <label>
        Email
        <input
          data-testid="sign-in-email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        Password
        <input
          data-testid="sign-in-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      <button className="primary full" type="submit" data-testid="sign-in-submit" disabled={busy}>
        {busy ? 'Signing in…' : submitLabel}
      </button>
    </form>
  )
}
