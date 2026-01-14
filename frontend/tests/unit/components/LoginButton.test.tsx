import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginButton } from '../../../src/components/LoginButton';

describe('LoginButton', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it('should render login button', () => {
    render(<LoginButton username="TestUser" />);

    expect(screen.getByRole('button', { name: /login with strava/i })).toBeInTheDocument();
  });

  it('should redirect to login URL when clicked', () => {
    render(<LoginButton username="TestUser" />);

    const button = screen.getByRole('button', { name: /login with strava/i });
    fireEvent.click(button);

    expect(window.location.href).toContain('/login/TestUser');
  });

  it('should encode username with special characters', () => {
    render(<LoginButton username="Test User" />);

    const button = screen.getByRole('button', { name: /login with strava/i });
    fireEvent.click(button);

    expect(window.location.href).toContain('/login/Test%20User');
  });
});
