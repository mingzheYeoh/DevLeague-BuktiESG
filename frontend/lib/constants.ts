/**
 * Values that must stay in step with the server.
 *
 * Kept in one place so a client-side guard can never quietly disagree with the
 * limit the API actually enforces.
 */

/** `backend/app/config.py::Settings.max_upload_bytes` (10 MB).
 *
 * The server is the authority: it returns 413 FILE_TOO_LARGE with the real
 * `max_bytes` in the error details. This constant only exists so the UI can
 * reject an oversized file before spending time uploading it. */
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024
