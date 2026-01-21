import { useNavigate } from 'react-router-dom';
import { AthleteProfile } from '../components/AthleteProfile';

export function DashboardPage() {
  const navigate = useNavigate();

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <header className="flex justify-between items-center mb-8 pb-4 border-b border-gray-200">
        <h1 className="m-0 text-2xl">Dashboard</h1>
        <button
          onClick={() => navigate('/')}
          className="py-2 px-4 rounded bg-gray-600 text-white hover:bg-gray-700 cursor-pointer"
        >
          Logout
        </button>
      </header>

      <main>
        <section className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
          <h2 className="mt-0 mb-4">Your Profile</h2>
          <AthleteProfile />
        </section>
      </main>
    </div>
  );
}
