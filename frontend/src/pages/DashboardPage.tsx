import { useNavigate } from 'react-router-dom';
import { AthleteProfile } from '../components/AthleteProfile';
import { LoginButton } from '../components/LoginButton';
import { useAuth } from '../context/AuthContext';
import { useAthlete } from '../hooks/useAthlete';

export function DashboardPage() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const { athlete, loading: stravaLoading, error: stravaError } = useAthlete();
  const stravaConnected = !!athlete;

  console.log('[Dashboard] Strava status:', { stravaConnected, stravaLoading, stravaError });

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <header className="flex justify-between items-center mb-8 pb-4 border-b border-gray-200">
        <h1 className="m-0 text-2xl">Dashboard</h1>
        <button
          onClick={handleLogout}
          className="py-2 px-4 rounded bg-gray-600 text-white hover:bg-gray-700 cursor-pointer"
        >
          Logout
        </button>
      </header>

      <main className="flex flex-col gap-6">
        {!stravaConnected && !stravaLoading && (
          <section className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="mt-0 mb-4">Connect Strava</h2>
            <p className="text-gray-500 mb-4">Link your Strava account to view your activities and profile.</p>
            <LoginButton username={user?.display_name ?? user?.email ?? 'Athlete'} />
          </section>
        )}

        {stravaLoading && (
          <section className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <p className="text-gray-500 italic">Checking Strava connection...</p>
          </section>
        )}

        {stravaConnected && (
          <section className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="mt-0 mb-4">Your Profile</h2>
            <AthleteProfile />
          </section>
        )}
      </main>
    </div>
  );
}
