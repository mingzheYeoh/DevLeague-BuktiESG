'use client'

import BuktiApp from '@/components/bukti-app'
import { AuthScreen } from '@/components/auth/auth-screen'
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
  const { state } = useSession()

  // Never the workspace before the actor is known. Rendering it and then
  // taking it away is worse than a brief wait.
  if (state === 'loading') return <Loading label="Checking your session…" />
  if (state === 'anonymous') return <AuthScreen />
  return <BuktiApp />
}
