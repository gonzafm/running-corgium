import { http, HttpResponse } from 'msw';
import type { Athlete, AuthorizeResponse } from '../../src/api/types';

export const mockAthlete: Athlete = {
  id: 123456,
  firstname: 'Gonzalo',
  lastname: 'Test',
  username: 'gonzalo_test',
  city: 'Madrid',
  country: 'Spain',
  premium: true,
};

export const handlers = [
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
