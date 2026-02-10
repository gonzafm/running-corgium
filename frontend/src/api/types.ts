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

// Auth types
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  first_name?: string;
  last_name?: string;
  display_name?: string;
}

// Cognito types
export interface CognitoTokenResponse {
  id_token: string;
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

export interface CognitoUser {
  sub: string;
  email: string;
}

// Error response shape
export interface ApiError {
  detail?: string;
  message?: string;
}
