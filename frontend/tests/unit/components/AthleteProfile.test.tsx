import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AthleteProfile } from '../../../src/components/AthleteProfile';

describe('AthleteProfile', () => {
  it('should show loading state initially', () => {
    render(<AthleteProfile />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should display athlete name after loading', async () => {
    render(<AthleteProfile />);

    await waitFor(() => {
      expect(screen.getByText('Gonzalo Test')).toBeInTheDocument();
    });
  });

  it('should display athlete location', async () => {
    render(<AthleteProfile />);

    await waitFor(() => {
      expect(screen.getByText('Madrid, Spain')).toBeInTheDocument();
    });
  });

  it('should display premium badge for premium members', async () => {
    render(<AthleteProfile />);

    await waitFor(() => {
      expect(screen.getByText('Premium Member')).toBeInTheDocument();
    });
  });
});
