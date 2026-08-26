'use client'

import { useState } from 'react'

import { api, errorMessage } from '@/lib/api'

import { ErrorNotice, Mark } from '../primitives'
import { SignInForm } from './sign-in-form'

export function AuthScreen() {
  const [mode, setMode] = useState<'sign-in' | 'register'>('sign-in')
  const [registeredEmail, setRegisteredEmail] = useState('')
  const [notice, setNotice] = useState<string | null>(null)

  return (
    <div className="auth-page">
      <section className="auth-card">
        <div className="brand">
          <Mark />
          <div>
            <strong>
              Bukti<span>ESG</span>
            </strong>
            <small>Evidence operations</small>
          </div>
        </div>

        {notice ? <p className="auth-notice">{notice}</p> : null}

        {mode === 'sign-in' ? (
          <>
            <h1>Sign in</h1>
            <SignInForm initialEmail={registeredEmail} key={registeredEmail} />
            <p className="field-hint">
              No account yet?{' '}
              <button
                className="link"
                type="button"
                data-testid="show-register"
                onClick={() => {
                  setNotice(null)
                  setMode('register')
                }}
              >
                Create one
              </button>
            </p>
          </>
        ) : (
          <RegisterForm
            onRegistered={(email) => {
              setRegisteredEmail(email)
              // Deliberately not the server's "check your email to finish
              // signing up". Task 11 has not landed, so no email is sent, and
              // repeating that line would strand the user.
              //
              // This copy is also correct for someone who already had an
              // account: registration returns an identical response either
              // way (anti-enumeration), and "sign in below" is the right
              // instruction for both readers. Change this line when email
              // verification lands and becomes a precondition of signing in.
              setNotice('Account created. Sign in below.')
              setMode('sign-in')
            }}
            onCancel={() => setMode('sign-in')}
          />
        )}
      </section>
    </div>
  )
}

function RegisterForm({
  onRegistered,
  onCancel,
}: {
  onRegistered: (email: string) => void
  onCancel: () => void
}) {
  const [email, setEmail] = useState('')
  const [organization, setOrganization] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const passwordTooShort = password.length > 0 && password.length < 12

  async function submit() {
    setError(null)
    setBusy(true)
    try {
      await api.register({
        email: email.trim(),
        password,
        organization_name: organization.trim(),
      })
      onRegistered(email.trim())
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      className="auth-form"
      data-testid="register-form"
      onSubmit={(e) => {
        e.preventDefault()
        void submit()
      }}
    >
      <h1>Create an account</h1>
      {error ? <ErrorNotice title="Could not create the account" message={error} /> : null}
      <label>
        Email
        <input
          data-testid="register-email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        Organization
        <input
          data-testid="register-org"
          value={organization}
          onChange={(e) => setOrganization(e.target.value)}
          placeholder="Your company's registered name"
          required
        />
      </label>
      <label>
        Password
        <input
          data-testid="register-password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          aria-invalid={passwordTooShort}
        />
      </label>
      <p className="field-hint">
        At least 12 characters. The server rejects anything shorter.
      </p>
      <button
        className="primary full"
        type="submit"
        data-testid="register-submit"
        disabled={busy || password.length < 12}
      >
        {busy ? 'Creating…' : 'Create account'}
      </button>
      <button className="link" type="button" onClick={onCancel}>
        Back to sign in
      </button>
    </form>
  )
}
