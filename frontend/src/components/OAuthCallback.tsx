import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { stravaApi } from '../api/strava';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);
  const hasAuthorized = useRef(false);

  useEffect(() => {
    // Prevent double execution in React strict mode (codes are single-use)
    if (hasAuthorized.current) {
      return;
    }

    const code = searchParams.get('code');

    if (!code) {
      setStatus('error');
      setError('No authorization code provided');
      return;
    }

    hasAuthorized.current = true;

    const authorize = async () => {
      try {
        console.log('Authorizing with code:', code);
        const response = await stravaApi.authorize(code);
        console.log('Strava authorization response:', response.message);
        setStatus('success');
        setTimeout(() => navigate('/athlete'), 1500);
      } catch (err) {
        console.error('Authorization failed:', err);
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
      <p>Redirecting to athlete profile...</p>
    </div>
  );
}
