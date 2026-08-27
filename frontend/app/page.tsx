'use client'

import BuktiApp from '@/components/bukti-app'
import { AuthScreen } from '@/components/auth/auth-screen'
import { ReauthOverlay } from '@/components/auth/reauth-overlay'
import { Loading } from '@/components/primitives'
import { SessionProvider, useSession } from '@/lib/session'

export default function Page() {
  return (
    <SessionProvider>
      <Gate />
    </SessionProvider>
  )
}

function Gate() {
  const { state, reauthNeeded } = useSession()

  // Never the workspace before the actor is known. Rendering it and then
  // taking it away is worse than a brief wait.
  if (state === 'loading') return <Loading label="Checking your session…" />
  if (state === 'anonymous') return <AuthScreen />
  return (
    <>
      {/* `inert` is what makes the overlay's aria-modal="true" honest: it
          removes this subtree from the focus order AND the accessibility
          tree. Without it a keyboard user tabs into a dead session and
          collects another 401 per click, while a screen reader has already
          been told the workspace is unavailable. */}
      <div inert={reauthNeeded}>
        <BuktiApp />
      </div>
      {reauthNeeded ? <ReauthOverlay /> : null}
    </>
  )
}
