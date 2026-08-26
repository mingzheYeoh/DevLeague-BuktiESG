'use client'

/**
 * Shown when a live session dies.
 *
 * A modal rather than a redirect to the sign-in screen, because the workspace
 * underneath stays mounted and its unsent input survives. A 14-day session can
 * expire in the middle of a long review justification, and losing that is a
 * worse outcome than the expiry.
 *
 * Not dismissible: there is nothing behind it the user can act on, and a close
 * button would only produce another 401.
 */
import { useSession } from '@/lib/session'

import { SignInForm } from './sign-in-form'

export function ReauthOverlay() {
  const { actor } = useSession()

  return (
    <div className="reauth-scrim" data-testid="reauth-overlay" role="dialog" aria-modal="true">
      <section className="auth-card reauth-card">
        <h1>Your session ended</h1>
        <p className="field-hint">
          Sign in again to carry on. Nothing you have typed has been lost.
        </p>
        {/* A dialog that appears without taking focus leaves a screen-reader
            user with no signal it exists. */}
        <SignInForm
          initialEmail={actor?.email ?? ''}
          submitLabel="Sign in and continue"
          autoFocus
        />
      </section>
    </div>
  )
}
