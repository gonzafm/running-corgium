import { useEffect, useState } from 'react';
import { stravaApi } from '../api/strava';
import type { Athlete } from '../api/types';

export function AthleteProfile() {
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAthlete = async () => {
      try {
        const data = await stravaApi.getAthlete();
        setAthlete(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch athlete');
      } finally {
        setLoading(false);
      }
    };

    fetchAthlete();
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!athlete) {
    return <div>No athlete data</div>;
  }

  return (
    <div className="athlete-profile">
      <h2>{athlete.firstname} {athlete.lastname}</h2>
      {athlete.city && athlete.country && (
        <p>{athlete.city}, {athlete.country}</p>
      )}
      {athlete.premium && <span className="premium-badge">Premium Member</span>}
    </div>
  );
}
