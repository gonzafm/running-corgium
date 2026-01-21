import { useEffect, useState, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { stravaApi } from '../api/strava';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const code = useMemo(() => searchParams.get('code'), [searchParams]);
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(
    code ? 'loading' : 'error'
  );
  const [error, setError] = useState<string | null>(
    code ? null : 'No authorization code provided'
  );
  const hasAuthorized = useRef(false);

  useEffect(() => {
    // Skip if no code or already authorized (prevents double execution in React strict mode)
    if (!code || hasAuthorized.current) {
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
  }, [code, navigate]);

  if (status === 'loading') {
    return (
      <div className="text-center p-8">
        <h2 className="mb-4">Authorizing...</h2>
        <p>Please wait while we complete your login.</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="text-center p-8">
        <h2 className="mb-4">Authorization Failed</h2>
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={() => navigate('/')}
          className="py-2 px-4 rounded bg-[#14b8a6] text-white hover:bg-[#0d9488] cursor-pointer"
        >
          Back to Home
        </button>
      </div>
    );
  }

  return (
    <div className="text-center p-8">
      <h2 className="mb-4">Success!</h2>
      <p>Redirecting to athlete profile...</p>
    </div>
  );
}
