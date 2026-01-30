import { useEffect, useState } from 'react';
import { stravaApi } from '../api/strava';
import type { Athlete } from '../api/types';

interface UseAthleteResult {
  athlete: Athlete | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAthlete(): UseAthleteResult {
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAthlete = async () => {
    setLoading(true);
    setError(null);
    console.log('[useAthlete] Fetching athlete data...');
    try {
      const data = await stravaApi.getAthlete();
      console.log('[useAthlete] Athlete loaded:', data.firstname);
      setAthlete(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch athlete';
      console.warn('[useAthlete] Failed to fetch athlete:', message);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAthlete();
  }, []);

  return { athlete, loading, error, refetch: fetchAthlete };
}
