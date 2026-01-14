import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { stravaApi } from '../api/strava';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');

    if (!code) {
      setStatus('error');
      setError('No authorization code provided');
      return;
    }

    const authorize = async () => {
      try {
        await stravaApi.authorize(code);
        setStatus('success');
        setTimeout(() => navigate('/dashboard'), 1500);
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Authorization failed');
      }
    };

    authorize();
  }, [searchParams, navigate]);

  if (status === 'loading') {
    return (
      <div className="oauth-callback">
        <h2>Authorizing...</h2>
        <p>Please wait while we complete your login.</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="oauth-callback">
        <h2>Authorization Failed</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    );
  }

  return (
    <div className="oauth-callback">
      <h2>Success!</h2>
      <p>Redirecting to dashboard...</p>
    </div>
  );
}
