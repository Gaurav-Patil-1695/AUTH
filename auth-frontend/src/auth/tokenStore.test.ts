import { getAccessToken, setAccessToken, clearTokens } from './tokenStore';

// The module uses a module-level variable, so we need to reset between tests.
// Since Jest caches modules, the state persists; we clear manually.

beforeEach(() => {
  clearTokens();
});

describe('tokenStore', () => {
  describe('getAccessToken', () => {
    it('returns null initially', () => {
      expect(getAccessToken()).toBeNull();
    });

    it('returns the token after setAccessToken', () => {
      setAccessToken('my-token');
      expect(getAccessToken()).toBe('my-token');
    });

    it('returns the latest token after multiple sets', () => {
      setAccessToken('first');
      setAccessToken('second');
      expect(getAccessToken()).toBe('second');
    });
  });

  describe('setAccessToken', () => {
    it('stores the token so getAccessToken returns it', () => {
      setAccessToken('abc123');
      expect(getAccessToken()).toBe('abc123');
    });

    it('overwrites a previous token', () => {
      setAccessToken('old');
      setAccessToken('new');
      expect(getAccessToken()).toBe('new');
    });
  });

  describe('clearTokens', () => {
    it('sets the token back to null', () => {
      setAccessToken('some-token');
      clearTokens();
      expect(getAccessToken()).toBeNull();
    });

    it('is safe to call when already null', () => {
      expect(() => clearTokens()).not.toThrow();
      expect(getAccessToken()).toBeNull();
    });

    it('can be called multiple times without error', () => {
      setAccessToken('tok');
      clearTokens();
      clearTokens();
      expect(getAccessToken()).toBeNull();
    });
  });
});
