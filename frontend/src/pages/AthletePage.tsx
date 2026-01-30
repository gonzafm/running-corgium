import { useNavigate } from 'react-router-dom';
import { AthleteProfile } from '../components/AthleteProfile';
import { useAuth } from '../context/AuthContext';

export function AthletePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <header className="flex justify-between items-center mb-8 pb-4 border-b border-gray-200">
        <h1 className="m-0 text-2xl">Athlete Profile</h1>
        <nav className="flex gap-2">
          <button
            onClick={() => navigate('/dashboard')}
            className="py-2 px-4 rounded bg-[#14b8a6] text-white hover:bg-[#0d9488] cursor-pointer"
          >
            Dashboard
          </button>
          <button
            onClick={handleLogout}
            className="py-2 px-4 rounded bg-gray-600 text-white hover:bg-gray-700 cursor-pointer"
          >
            Logout
          </button>
        </nav>
      </header>

      <main>
        <AthleteProfile />
      </main>
    </div>
  );
}
