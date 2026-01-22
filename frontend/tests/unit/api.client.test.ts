import { describe, it, expect } from 'vitest';
import { stravaApi } from '../../src/api/strava';
import { mockActivities } from '../mocks/handlers';

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

  describe('getActivities', () => {
    it('should return activities as an array', async () => {
      const activities = await stravaApi.getActivities();

      expect(Array.isArray(activities)).toBe(true);
      expect(activities.length).toBe(2);
    });

    it('should return activities with correct structure', async () => {
      const activities = await stravaApi.getActivities();
      const activity = activities[0];

      expect(activity.id).toBe(mockActivities[0].id);
      expect(activity.name).toBe(mockActivities[0].name);
      expect(activity.distance).toBe(mockActivities[0].distance);
      expect(activity.moving_time).toBe(mockActivities[0].moving_time);
      expect(activity.type).toBe(mockActivities[0].type);
    });

    it('should return activities with all required fields', async () => {
      const activities = await stravaApi.getActivities();

      for (const activity of activities) {
        expect(activity).toHaveProperty('id');
        expect(activity).toHaveProperty('name');
        expect(activity).toHaveProperty('distance');
        expect(activity).toHaveProperty('moving_time');
        expect(activity).toHaveProperty('elapsed_time');
        expect(activity).toHaveProperty('total_elevation_gain');
        expect(activity).toHaveProperty('type');
        expect(activity).toHaveProperty('start_date');
        expect(activity).toHaveProperty('start_date_local');
        expect(activity).toHaveProperty('timezone');
      }
    });

    it('should return different activity types', async () => {
      const activities = await stravaApi.getActivities();
      const types = activities.map((a) => a.type);

      expect(types).toContain('Run');
      expect(types).toContain('Ride');
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
