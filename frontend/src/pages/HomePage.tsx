import { useState } from 'react';
import { LoginButton } from '../components/LoginButton';

export function HomePage() {
  const [username, setUsername] = useState('');

  return (
    <div className="text-center flex flex-col justify-center items-center w-full">
      <h1 className="text-4xl mb-2">Running Corgium</h1>
      <p className="text-gray-500 mb-8">Connect your Strava account to view your athlete profile.</p>

      <div className="flex flex-col gap-4 items-center max-w-[300px] mx-auto">
        <input
          type="text"
          placeholder="Enter your name"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          aria-label="Username"
          className="w-full py-3 px-3 text-base border border-gray-300 rounded focus:outline-none focus:border-[#14b8a6]"
        />
        <LoginButton username={username || 'Athlete'} />
      </div>
    </div>
  );
}
