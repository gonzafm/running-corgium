import { http, HttpResponse, passthrough } from 'msw';
import type { Athlete, AuthorizeResponse, Activity } from '../../src/api/types';

export const mockAthlete: Athlete = {
  id: 123456,
  firstname: 'Gonzalo',
  lastname: 'Test',
  username: 'gonzalo_test',
  city: 'Madrid',
  country: 'Spain',
  premium: true,
};

export const mockActivities: Activity[] = [
  {
    id: 1001,
    name: 'Morning Run',
    distance: 5000,
    moving_time: 1800,
    elapsed_time: 1920,
    total_elevation_gain: 50,
    type: 'Run',
    start_date: '2024-01-15T08:00:00Z',
    start_date_local: '2024-01-15T09:00:00',
    timezone: 'Europe/Madrid',
  },
  {
    id: 1002,
    name: 'Evening Ride',
    distance: 25000,
    moving_time: 3600,
    elapsed_time: 3900,
    total_elevation_gain: 200,
    type: 'Ride',
    start_date: '2024-01-14T17:00:00Z',
    start_date_local: '2024-01-14T18:00:00',
    timezone: 'Europe/Madrid',
  },
];

// Backend URL for integration tests - let these pass through to real server
const BACKEND_URL = 'http://localhost:8000';

export const handlers = [
  // Passthrough handlers for integration tests (must be first to take priority)
  http.get(`${BACKEND_URL}/*`, () => passthrough()),
  http.post(`${BACKEND_URL}/*`, () => passthrough()),

  // GET /strava/authorize - OAuth callback
  http.get('/strava/authorize', ({ request }) => {
    const url = new URL(request.url);
    const code = url.searchParams.get('code');

    if (!code) {
      return HttpResponse.json({ detail: 'Missing code' }, { status: 400 });
    }

    return HttpResponse.json({ message: code } satisfies AuthorizeResponse);
  }),

  // GET /strava/athlete - Get athlete data
  http.get('/strava/athlete', () => {
    return HttpResponse.json(mockAthlete);
  }),

  // GET /strava/activities - Get activities list
  http.get('/strava/activities', () => {
    return HttpResponse.json(mockActivities);
  }),

  // GET /login/:name - Redirect to Strava OAuth
  http.get('/login/:name', () => {
    return new HttpResponse(null, {
      status: 307,
      headers: {
        Location: 'https://www.strava.com/oauth/authorize?client_id=12345',
      },
    });
  }),
];
