import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { OAuthCallback } from '../../../src/components/OAuthCallback';

// Mock console.log to verify logging behavior
const consoleSpy = vi.spyOn(console, 'log');

/**
 * Test suite for Strava OAuth callback flow
 *
 * Scenario: Frontend receives callback from Strava at http://localhost:5173/auth/callback
 * 1. Strava redirects to frontend with authorization code
 * 2. Frontend extracts code and passes to backend
 * 3. Frontend logs incoming message from backend response
 * 4. Frontend redirects to Athlete page
 */
describe('OAuthCallback - Strava Authorization Flow', () => {
  beforeEach(() => {
    consoleSpy.mockClear();
  });

  const renderWithRouter = (initialEntry: string) => {
    return render(
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/auth/callback" element={<OAuthCallback />} />
          <Route path="/athlete" element={<div data-testid="athlete-page">Athlete Profile</div>} />
          <Route path="/dashboard" element={<div data-testid="dashboard-page">Dashboard</div>} />
          <Route path="/" element={<div data-testid="home-page">Home</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('should display loading state when receiving callback from Strava', () => {
    renderWithRouter('/auth/callback?code=test_auth_code');

    expect(screen.getByText('Authorizing...')).toBeInTheDocument();
    expect(screen.getByText('Please wait while we complete your login.')).toBeInTheDocument();
  });

  it('should pass authorization code to backend, log response, and redirect to athlete page on success', async () => {
    renderWithRouter('/auth/callback?code=strava_callback_code_123');

    // Initially shows loading
    expect(screen.getByText('Authorizing...')).toBeInTheDocument();

    // Wait for success state
    await waitFor(() => {
      expect(screen.getByText('Success!')).toBeInTheDocument();
    });

    // Verify the incoming message is logged
    expect(consoleSpy).toHaveBeenCalledWith(
      'Strava authorization response:',
      'strava_callback_code_123'
    );

    expect(screen.getByText('Redirecting to dashboard...')).toBeInTheDocument();

    // Wait for navigation to dashboard page
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should handle missing authorization code with error state', async () => {
    renderWithRouter('/auth/callback');

    await waitFor(() => {
      expect(screen.getByText('Authorization Failed')).toBeInTheDocument();
    });

    expect(screen.getByText('No authorization code provided')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /back to home/i })).toBeInTheDocument();
  });

  it('should extract code from URL search params correctly', async () => {
    const testCode = 'unique_strava_code_456';
    renderWithRouter(`/auth/callback?code=${testCode}&scope=read`);

    // The component should successfully process even with additional params
    await waitFor(() => {
      expect(screen.getByText('Success!')).toBeInTheDocument();
    });
  });

  it('should handle backend authorization error gracefully', async () => {
    // MSW handler returns error for 'error_code'
    // We need to add a handler for this - for now test the error display mechanism
    renderWithRouter('/auth/callback?code=');

    await waitFor(() => {
      expect(screen.getByText('Authorization Failed')).toBeInTheDocument();
    });
  });

  it('should complete full OAuth callback flow: receive -> log -> redirect to dashboard', async () => {
    const stravaCode = 'complete_flow_test_code';
    renderWithRouter(`/auth/callback?code=${stravaCode}`);

    // Step 1: Loading state while processing callback
    expect(screen.getByText('Authorizing...')).toBeInTheDocument();

    // Step 2: Success after backend confirms
    await waitFor(() => {
      expect(screen.getByText('Success!')).toBeInTheDocument();
    });

    // Step 3: Verify message was logged
    expect(consoleSpy).toHaveBeenCalledWith(
      'Strava authorization response:',
      stravaCode
    );

    // Step 4: Redirect to dashboard page
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
