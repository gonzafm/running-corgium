import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HomePage } from '../../../src/pages/HomePage';

describe('HomePage', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it('should render the title', () => {
    render(<HomePage />);

    expect(screen.getByRole('heading', { name: /running corgium/i })).toBeInTheDocument();
  });

  it('should render username input', () => {
    render(<HomePage />);

    expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument();
  });

  it('should render login button', () => {
    render(<HomePage />);

    expect(screen.getByRole('button', { name: /login with strava/i })).toBeInTheDocument();
  });

  it('should use default username when input is empty', () => {
    render(<HomePage />);

    const button = screen.getByRole('button', { name: /login with strava/i });
    fireEvent.click(button);

    expect(window.location.href).toContain('/login/Athlete');
  });

  it('should use entered username for login', () => {
    render(<HomePage />);

    const input = screen.getByRole('textbox', { name: /username/i });
    fireEvent.change(input, { target: { value: 'TestUser' } });

    const button = screen.getByRole('button', { name: /login with strava/i });
    fireEvent.click(button);

    expect(window.location.href).toContain('/login/TestUser');
  });
});
