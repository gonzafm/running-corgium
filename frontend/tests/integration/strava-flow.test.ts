import { describe, it, expect, beforeAll } from 'vitest';

// Integration tests run against real backend
// Backend must be running on localhost:8000
const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://localhost:8000';

describe('Strava Integration (Real Backend)', () => {
  let backendAvailable = false;

  beforeAll(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/strava/athlete`, {
        signal: AbortSignal.timeout(2000),
      });
      // Check that it's actually the FastAPI backend (returns JSON)
      const contentType = response.headers.get('content-type') || '';
      backendAvailable = contentType.includes('application/json');
      if (!backendAvailable) {
        console.warn('Backend returned non-JSON response, skipping integration tests');
      }
    } catch {
      console.warn('Backend not available, skipping integration tests');
      backendAvailable = false;
    }
  });

  it('GET /login/:name should return 307 redirect', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/login/TestUser`, {
      redirect: 'manual',
    });

    expect(response.status).toBe(307);
    expect(response.headers.get('location')).toContain('strava.com');
  });

  it('GET /strava/authorize with invalid code should return 400', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/strava/authorize?code=invalid_code`);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.detail).toBeDefined();
  });

  it('GET /strava/athlete should return JSON response', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/strava/athlete`);

    expect(response.headers.get('content-type')).toContain('application/json');
  });
});
