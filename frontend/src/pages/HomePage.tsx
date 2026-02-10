import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { config } from '../config';
import { cognitoApi } from '../api/cognito';

type Mode = 'login' | 'register';

export function HomePage() {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (mode === 'register' && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setSubmitting(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError(null);
    setConfirmPassword('');
  };

  if (config.authMode === 'cognito') {
    return (
      <div className="text-center flex flex-col justify-center items-center w-full">
        <h1 className="text-4xl mb-2">Running Corgium</h1>
        <p className="text-gray-500 mb-8">Sign in to your account</p>

        <button
          onClick={() => {
            window.location.href = cognitoApi.getLoginUrl();
          }}
          className="py-3 px-6 rounded bg-[#14b8a6] text-white hover:bg-[#0d9488] cursor-pointer max-w-[300px] w-full"
        >
          Sign in
        </button>
      </div>
    );
  }

  return (
    <div className="text-center flex flex-col justify-center items-center w-full">
      <h1 className="text-4xl mb-2">Running Corgium</h1>
      <p className="text-gray-500 mb-8">
        {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
      </p>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 items-center max-w-[300px] w-full mx-auto"
      >
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Email"
          required
          className="w-full py-3 px-3 text-base border border-gray-300 rounded focus:outline-none focus:border-[#14b8a6]"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label="Password"
          required
          className="w-full py-3 px-3 text-base border border-gray-300 rounded focus:outline-none focus:border-[#14b8a6]"
        />
        {mode === 'register' && (
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            aria-label="Confirm password"
            required
            className="w-full py-3 px-3 text-base border border-gray-300 rounded focus:outline-none focus:border-[#14b8a6]"
          />
        )}

        {error && <p className="text-red-500 text-sm m-0">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 px-6 rounded bg-[#14b8a6] text-white hover:bg-[#0d9488] cursor-pointer disabled:opacity-50"
        >
          {submitting
            ? 'Please wait...'
            : mode === 'login'
              ? 'Sign in'
              : 'Register'}
        </button>

        <button
          type="button"
          onClick={toggleMode}
          className="text-[#14b8a6] hover:underline bg-transparent border-none cursor-pointer text-sm"
        >
          {mode === 'login'
            ? "Don't have an account? Register"
            : 'Already have an account? Sign in'}
        </button>
      </form>
    </div>
  );
}