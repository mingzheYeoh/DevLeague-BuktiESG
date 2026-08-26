/**
 * Shared network stubs for the browser specs.
 *
 * `CORS_HEADERS` used to be `const CORS = { 'Access-Control-Allow-Origin': '*' }`
 * copied into five spec files. A wildcard origin is rejected by the browser in
 * a credentialed request, so all five had to change at once when the client
 * started sending the session cookie - which is exactly why it is one module
 * now rather than five constants that happen to agree.
 */
export const APP_ORIGIN = 'http://localhost:3000'

export const CORS_HEADERS = {
  'Access-Control-Allow-Origin': APP_ORIGIN,
  'Access-Control-Allow-Credentials': 'true',
}
