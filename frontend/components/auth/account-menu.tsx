'use client'

import { LogOut } from 'lucide-react'

import { useSession } from '@/lib/session'

import { Drawer, Key } from '../primitives'

export function AccountMenu({ close }: { close: () => void }) {
  const { actor, signOut } = useSession()
  if (!actor) return null

  return (
    <Drawer eyebrow="Account" title={actor.email} close={close}>
      <Key label="Organization" value={actor.organization_name} />
      <Key label="Role" value={actor.role} />
      <div className="callout info">
        <div>
          <b>Reviews are signed by this account</b>
          <p>
            Every review verdict and evidence acceptance records the account shown above. The
            server takes it from your session — it is not a field you can type.
          </p>
        </div>
      </div>
      <button
        className="secondary full"
        type="button"
        data-testid="sign-out"
        onClick={() => void signOut()}
      >
        <LogOut />
        Sign out
      </button>
    </Drawer>
  )
}
