import { useEffect, useState } from 'react';
import { stravaApi } from '../api/strava';
import type {Activity, Athlete} from '../api/types';

export function AthleteProfile() {
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAthlete = async () => {
      try {
        const data = await stravaApi.getAthlete();
        const activityResponse = await stravaApi.getActivities();
        setAthlete(data);
        setActivities(activityResponse);
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

      <h3 className="mt-4 mb-2">Recent Activities</h3>
      <table className="border-collapse w-full">
        <thead>
          <tr>
            <th className="py-2 px-4 border border-teal-900 bg-teal-900 text-teal-50">Name</th>
            <th className="py-2 px-4 border border-teal-900 bg-teal-900 text-teal-50">Type</th>
            <th className="py-2 px-4 border border-teal-900 bg-teal-900 text-teal-50">Distance</th>
            <th className="py-2 px-4 border border-teal-900 bg-teal-900 text-teal-50">Date</th>
          </tr>
        </thead>
        <tbody>
          {activities.map((activity, index) => (
            <tr key={index} className="odd:bg-teal-500 even:bg-teal-100 border-teal-300 border-teal-300">
              <td className="py-2 px-4  ">{activity.name}</td>
              <td className="py-2 px-4  ">{activity.type}</td>
              <td className="py-2 px-4  ">{activity.distance} km</td>
              <td className="py-2 px-4  ">{activity.start_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
