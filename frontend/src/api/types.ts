// Response from GET /strava/authorize?code={code}
export interface AuthorizeResponse {
  message: string;
}

// Athlete data from GET /strava/athlete
// Based on Strava API athlete model
export interface Athlete {
  id: number;
  firstname: string;
  lastname?: string;
  username?: string;
  profile?: string;
  profile_medium?: string;
  city?: string;
  state?: string;
  country?: string;
  sex?: 'M' | 'F';
  premium?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Activity {
  id: number;
  name: string;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  total_elevation_gain: number;
  type: 'Ride' | 'Run' | 'Swim' | 'Hike' | 'Workout';
  start_date: string;
  start_date_local: string;
  timezone: string;
}

// Error response shape
export interface ApiError {
  detail?: string;
  message?: string;
}
