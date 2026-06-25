// Thin fetch wrapper. credentials:'include' carries the session cookie; in dev the
// Vite proxy makes /api same-origin so this just works.
export async function api(path, options = {}) {
  const resp = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!resp.ok) {
    const err = new Error(`API ${resp.status}`)
    err.status = resp.status
    throw err
  }
  if (resp.status === 204) return null
  return resp.json()
}
