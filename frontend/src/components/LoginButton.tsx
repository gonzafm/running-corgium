import { stravaApi } from '../api/strava';

interface LoginButtonProps {
  username: string;
}

export function LoginButton({ username }: LoginButtonProps) {
  const handleLogin = () => {
    window.location.href = stravaApi.getLoginUrl(username);
  };

  return (
    <button onClick={handleLogin} type="button">
      Login with Strava
    </button>
  );
}
