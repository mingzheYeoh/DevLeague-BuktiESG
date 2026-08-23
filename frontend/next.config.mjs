/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // `typescript.ignoreBuildErrors` was set to true by the original v0 scaffold,
  // which meant a production build shipped regardless of type errors. Removed
  // once the app typechecked cleanly against the real API types — a client
  // whose wire types have drifted from the server should fail the build, not
  // reach the browser.
  images: {
    unoptimized: true,
  },
}

export default nextConfig
