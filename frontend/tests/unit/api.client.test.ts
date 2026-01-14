import { describe, it, expect } from 'vitest';
import { stravaApi } from '../../src/api/strava';

describe('Strava API Client', () => {
  describe('authorize', () => {
    it('should return message with the code', async () => {
      const result = await stravaApi.authorize('test_code');

      expect(result.message).toBe('test_code');
    });

    it('should handle different codes', async () => {
      const result = await stravaApi.authorize('another_code');

      expect(result.message).toBe('another_code');
    });
  });

  describe('getAthlete', () => {
    it('should return athlete data', async () => {
      const athlete = await stravaApi.getAthlete();

      expect(athlete.id).toBe(123456);
      expect(athlete.firstname).toBe('Gonzalo');
    });

    it('should return athlete with optional fields', async () => {
      const athlete = await stravaApi.getAthlete();

      expect(athlete.city).toBe('Madrid');
      expect(athlete.country).toBe('Spain');
      expect(athlete.premium).toBe(true);
    });
  });

  describe('getLoginUrl', () => {
    it('should construct correct login URL', () => {
      const url = stravaApi.getLoginUrl('TestUser');

      expect(url).toContain('/login/TestUser');
    });

    it('should encode special characters in name', () => {
      const url = stravaApi.getLoginUrl('Test User');

      expect(url).toContain('/login/Test%20User');
    });
  });
});
