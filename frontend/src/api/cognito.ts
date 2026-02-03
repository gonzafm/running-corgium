import { config } from '../config';
import type { CognitoTokenResponse, CognitoUser } from './types';

const { domain, clientId, redirectUri } = config.cognito;

export const cognitoApi = {
  getLoginUrl(): string {
    const params = new URLSearchParams({
      client_id: clientId,
      response_type: 'code',
      scope: 'openid email',
      redirect_uri: redirectUri,
    });
    return `https://${domain}/login?${params}`;
  },

  getLogoutUrl(): string {
    const params = new URLSearchParams({
      client_id: clientId,
      logout_uri: window.location.origin,
    });
    return `https://${domain}/logout?${params}`;
  },

  async exchangeCode(code: string): Promise<CognitoTokenResponse> {
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: clientId,
      code,
      redirect_uri: redirectUri,
    });

    const response = await fetch(`https://${domain}/oauth2/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });

    if (!response.ok) {
      throw new Error(`Token exchange failed: ${response.status}`);
    }

    return response.json();
  },

  parseIdToken(idToken: string): CognitoUser {
    const payload = idToken.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    return {
      sub: decoded.sub,
      email: decoded.email || '',
    };
  },

  isTokenExpired(idToken: string): boolean {
    try {
      const payload = idToken.split('.')[1];
      const decoded = JSON.parse(atob(payload));
      return decoded.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  },
};