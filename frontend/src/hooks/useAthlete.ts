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
    try {
      const data = await stravaApi.getAthlete();
      setAthlete(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch athlete');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAthlete();
  }, []);

  return { athlete, loading, error, refetch: fetchAthlete };
}
