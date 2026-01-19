import { useNavigate } from 'react-router-dom';
import { AthleteProfile } from '../components/AthleteProfile';

export function AthletePage() {
  const navigate = useNavigate();

  return (
    <div className="athlete-page">
      <header>
        <h1>Athlete Profile</h1>
        <nav>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/')}>Logout</button>
        </nav>
      </header>

      <main>
        <AthleteProfile />
      </main>
    </div>
  );
}
