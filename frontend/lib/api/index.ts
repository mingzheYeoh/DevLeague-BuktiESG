/**
 * BuktiESG API layer.
 *
 * `import { api, useCaseWorkspace } from '@/lib/api'`
 *
 * Layout:
 *   types.ts   wire shapes and enums, transcribed from backend/app
 *   client.ts  one function per real route, plus error normalisation
 *   status.ts  labels, colour tones and source-location rendering
 *   derive.ts  display-only tallies over server data
 *   hooks.ts   React state, fetching and mutations
 */
export * from './types'
export * from './client'
export * from './status'
export * from './derive'
export * from './hooks'
