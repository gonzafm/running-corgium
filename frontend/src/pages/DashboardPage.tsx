import { useNavigate } from 'react-router-dom';
import { AthleteProfile } from '../components/AthleteProfile';

export function DashboardPage() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page">
      <header>
        <h1>Dashboard</h1>
        <button onClick={() => navigate('/')}>Logout</button>
      </header>

      <main>
        <section className="athlete-section">
          <h2>Your Profile</h2>
          <AthleteProfile />
        </section>
      </main>
    </div>
  );
}
