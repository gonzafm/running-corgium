import { apiClient } from './client';
import type { AuthorizeResponse, Athlete, Activity } from './types';

export const stravaApi = {
  authorize: (code: string): Promise<AuthorizeResponse> => {
    return apiClient.get<AuthorizeResponse>(`/strava/authorize?code=${code}`);
  },

  getAthlete: (): Promise<Athlete> => {
    return apiClient.get<Athlete>('/strava/athlete');
  },

  getActivities: (): Promise<Activity[]> => {
    return apiClient.get<Activity[]>('/strava/activities');
  },

  getLoginUrl: (name: string): string => {
    return apiClient.getLoginUrl(name);
  },
};
