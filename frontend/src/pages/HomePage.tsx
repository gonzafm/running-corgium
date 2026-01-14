import { useState } from 'react';
import { LoginButton } from '../components/LoginButton';

export function HomePage() {
  const [username, setUsername] = useState('');

  return (
    <div className="home-page">
      <h1>Running Corgium</h1>
      <p>Connect your Strava account to view your athlete profile.</p>

      <div className="login-form">
        <input
          type="text"
          placeholder="Enter your name"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          aria-label="Username"
        />
        <LoginButton username={username || 'Athlete'} />
      </div>
    </div>
  );
}
