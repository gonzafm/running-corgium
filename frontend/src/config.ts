export const config = {
  authMode: (import.meta.env.VITE_AUTH_MODE || 'standalone') as
    | 'standalone'
    | 'cognito',
  cognito: {
    domain: import.meta.env.VITE_COGNITO_DOMAIN || '',
    clientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
    redirectUri:
      import.meta.env.VITE_COGNITO_REDIRECT_URI ||
      `${window.location.origin}/auth/callback`,
  },
};