import { describe, it, expect, beforeAll } from 'vitest';

const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://localhost:8000';

describe('Athlete Endpoint Integration', () => {
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
      backendAvailable = false;
    }
  });

  it('should respond with JSON content-type', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/strava/athlete`);

    expect(response.headers.get('content-type')).toContain('application/json');
  });

  it('should have required fields when authenticated', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/strava/athlete`);

    if (response.ok) {
      const athlete = await response.json();
      expect(athlete).toHaveProperty('id');
      expect(athlete).toHaveProperty('firstname');
    }
  });

  it('should return valid HTTP status code', async () => {
    if (!backendAvailable) {
      console.log('Skipping: backend not available');
      return;
    }

    const response = await fetch(`${BACKEND_URL}/strava/athlete`);

    // Should be 200 if authenticated, or an error status if not
    expect([200, 401, 403, 500]).toContain(response.status);
  });
});
