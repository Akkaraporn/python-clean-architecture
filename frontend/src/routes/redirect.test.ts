import { describe, expect, it } from 'vitest'

import { DEFAULT_AFTER_LOGIN, redirectTarget } from './redirect'

describe('redirectTarget', () => {
  it('returns to the page the user was trying to open', () => {
    expect(redirectTarget({ from: '/profile?tab=1#top' })).toBe('/profile?tab=1#top')
  })

  it.each([
    ['no state', null],
    ['no from', {}],
    ['not a string', { from: 42 }],
    ['absolute URL', { from: 'https://evil.example.com' }],
    ['protocol-relative URL', { from: '//evil.example.com' }],
    ['the login page itself', { from: '/login' }],
    ['the register page', { from: '/register' }],
  ])('falls back to the profile for %s', (_, state) => {
    expect(redirectTarget(state)).toBe(DEFAULT_AFTER_LOGIN)
  })
})
