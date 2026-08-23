'use client'

/**
 * The local reviewer identity.
 *
 * The backend has no authentication and no user table: every review and every
 * Action carries a free-text `reviewer_name` / `owner_name` that the client
 * supplies. So this is a *label*, not an identity — it proves nothing and
 * authorises nothing. It exists because the review endpoint requires a
 * non-blank reviewer_name, and retyping it on every verdict would be worse.
 *
 * Anything that needs real attribution needs real auth on the server first.
 */
import { useCallback, useEffect, useState } from 'react'

const REVIEWER_KEY = 'buktiesg.reviewerName'

export function useReviewer() {
  const [reviewerName, setReviewerNameState] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    setReviewerNameState(window.localStorage.getItem(REVIEWER_KEY) ?? '')
    setLoaded(true)
  }, [])

  const setReviewerName = useCallback((name: string) => {
    setReviewerNameState(name)
    if (typeof window === 'undefined') return
    if (name.trim()) window.localStorage.setItem(REVIEWER_KEY, name.trim())
    else window.localStorage.removeItem(REVIEWER_KEY)
  }, [])

  return { reviewerName, setReviewerName, loaded, hasReviewer: reviewerName.trim().length > 0 }
}
