import { stravaApi } from '../api/strava';

interface LoginButtonProps {
  username: string;
}

export function LoginButton({ username }: LoginButtonProps) {
  const handleLogin = () => {
    const url = stravaApi.getLoginUrl(username);
    console.log('[LoginButton] Redirecting to Strava OAuth:', url);
    window.location.href = url;
  };

  return (
    <button
      onClick={handleLogin}
      type="button"
      className="py-3 px-6 rounded bg-[#14b8a6] text-white hover:bg-[#0d9488] cursor-pointer"
    >
      Login with Strava
    </button>
  );
}
