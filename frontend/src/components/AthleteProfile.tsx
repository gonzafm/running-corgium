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
    return <div className="text-gray-500 italic">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  if (!athlete) {
    return <div>No athlete data</div>;
  }

  return (
    <div className="text-left">
      <h2 className="m-0 mb-2">{athlete.firstname} {athlete.lastname}</h2>
      {athlete.city && athlete.country && (
        <p className="text-gray-500 m-0 mb-2">{athlete.city}, {athlete.country}</p>
      )}
      {athlete.premium && (
        <span className="inline-block bg-[#14b8a6] text-white py-1 px-2 rounded text-sm">
          Premium Member
        </span>
      )}
    </div>
  );
}
