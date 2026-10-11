import { type Mock, vi } from 'vitest'

export type FetchMock = Mock<typeof fetch>

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Replaces global fetch; each call returns the next queued response. */
export function mockFetch(...responses: Response[]): FetchMock {
  const fetchMock: FetchMock = vi.fn<typeof fetch>()
  for (const response of responses) {
    fetchMock.mockResolvedValueOnce(response)
  }
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function requestHeaders(fetchMock: FetchMock, call = 0): Record<string, string> {
  const init = fetchMock.mock.calls[call]?.[1]
  return (init?.headers ?? {}) as Record<string, string>
}
