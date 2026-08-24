import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'BuktiESG · Evidence operations',
  description: 'Evidence-first ESG questionnaire response workspace for Malaysian SMEs.',
  generator: 'v0.app',
  // There was no favicon: `public/icon.svg` is a leftover of the v0 scaffold and
  // Next only auto-links icon files under `app/`, so the browser fell back to
  // /favicon.ico and got a 404. Pointing at the same asset the sidebar uses
  // keeps one file to replace.
  //
  // No `apple` entry: iOS ignores an SVG touch icon, so that slot needs a real
  // 180x180 PNG export rather than a declaration that silently does nothing.
  icons: {
    icon: [{ url: '/logo-mark.svg', type: 'image/svg+xml' }],
  },
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#ffffff',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="bg-background">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
