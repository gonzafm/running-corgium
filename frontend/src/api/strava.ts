import { apiClient } from './client';
import type { AuthorizeResponse, Athlete } from './types';

export const stravaApi = {
  authorize: (code: string): Promise<AuthorizeResponse> => {
    return apiClient.get<AuthorizeResponse>(`/strava/authorize?code=${code}`);
  },

  getAthlete: (): Promise<Athlete> => {
    return apiClient.get<Athlete>('/strava/athlete');
  },

  getLoginUrl: (name: string): string => {
    return apiClient.getLoginUrl(name);
  },
};
