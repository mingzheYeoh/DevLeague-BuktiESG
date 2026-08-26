'use client'

/**
 * Who is signed in, and what to do when that stops being true.
 *
 * There is no router and no `middleware.ts`, both deliberately. Middleware
 * would be worse than useless here: it can see that the session cookie exists
 * but not that it is valid, so a revoked session passes it and 401s at the API
 * anyway. It would also appear to work locally and break on deployment —
 * cookies are scoped by host and ignore port, so `localhost:8000`'s cookie is
 * readable by the Next server at `localhost:3000`, which stops being true the
 * day the two live on different domains.
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type { ActorSummary, LoginRequest } from '@/lib/api'
import { api, onSessionLost } from '@/lib/api'

type SessionState = 'loading' | 'authenticated' | 'anonymous'

interface SessionValue {
  state: SessionState
  actor: ActorSummary | null
  /** True when a live session died mid-use. Drives the overlay, not the gate:
   * the workspace stays mounted underneath so unsent form input survives. */
  reauthNeeded: boolean
  signIn: (body: LoginRequest) => Promise<void>
  signOut: () => Promise<void>
}

const SessionContext = createContext<SessionValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>('loading')
  const [actor, setActor] = useState<ActorSummary | null>(null)
  const [reauthNeeded, setReauthNeeded] = useState(false)

  const load = useCallback(async () => {
    try {
      const next = await api.me()
      setActor(next)
      setState('authenticated')
      setReauthNeeded(false)
    } catch {
      // Any failure to establish an actor is the same outcome: nobody is
      // signed in. A 401 and an unreachable API differ in cause, not in what
      // the browser may now show.
      setActor(null)
      setState('anonymous')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(
    () =>
      onSessionLost(() => {
        // Only meaningful while we believe we are signed in. Ignoring it
        // otherwise is the second of two opposing guards: `silentAuthFailure`
        // in the client stops `login` announcing at all, and this stops a
        // stray announcement raising an overlay over the sign-in screen.
        setState((current) => {
          if (current === 'authenticated') setReauthNeeded(true)
          return current
        })
      }),
    [],
  )

  const signIn = useCallback(
    async (body: LoginRequest) => {
      await api.login(body)
      await load()
    },
    [load],
  )

  const signOut = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // 401 here means the session was already gone, which is the state
      // logout was asking for. Any other failure leaves the cookie on the
      // server's terms, and there is nothing the browser can do about it —
      // either way this client is done with it.
    }
    setActor(null)
    setReauthNeeded(false)
    setState('anonymous')
  }, [])

  return (
    <SessionContext.Provider value={{ state, actor, reauthNeeded, signIn, signOut }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession must be used inside <SessionProvider>')
  return value
}
