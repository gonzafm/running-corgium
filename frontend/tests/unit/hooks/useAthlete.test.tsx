import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAthlete } from '../../../src/hooks/useAthlete';

describe('useAthlete', () => {
  it('should start with loading state', () => {
    const { result } = renderHook(() => useAthlete());

    expect(result.current.loading).toBe(true);
    expect(result.current.athlete).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should fetch athlete data', async () => {
    const { result } = renderHook(() => useAthlete());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.athlete).not.toBeNull();
    expect(result.current.athlete?.firstname).toBe('Gonzalo');
    expect(result.current.error).toBeNull();
  });

  it('should provide refetch function', async () => {
    const { result } = renderHook(() => useAthlete());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');
  });
});
