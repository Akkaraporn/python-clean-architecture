// localStorage is simple and survives reloads, but any script running on the page
// can read it, so an XSS bug would expose the token. An httpOnly cookie avoids that
// at the cost of CSRF handling and backend changes; see the README trade-offs.

export const TOKEN_STORAGE_KEY = 'auth.accessToken'

// Storage access can throw (privacy modes, disabled storage); treat that as "no token".
export const tokenStorage = {
  get(): string | null {
    try {
      return window.localStorage.getItem(TOKEN_STORAGE_KEY)
    } catch {
      return null
    }
  },
  set(token: string): void {
    try {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } catch {
      // The session still works in memory until the page is reloaded.
    }
  },
  clear(): void {
    try {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    } catch {
      // Nothing stored, nothing to clear.
    }
  },
}
