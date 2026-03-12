import { describe, it, expect } from 'vitest';
import {
  formatPower,
  formatLatency,
  getActionColor,
  getPriorityLabel,
  calculatePercentage,
} from '../utils';

describe('Utility Functions', () => {
  describe('formatPower', () => {
    it('formats watts correctly', () => {
      expect(formatPower(500)).toBe('500W');
      expect(formatPower(999)).toBe('999W');
    });

    it('formats kilowatts correctly', () => {
      expect(formatPower(1000)).toBe('1.0kW');
      expect(formatPower(1500)).toBe('1.5kW');
      expect(formatPower(999999)).toBe('1000.0kW');
    });

    it('formats megawatts correctly', () => {
      expect(formatPower(1000000)).toBe('1.0MW');
      expect(formatPower(2500000)).toBe('2.5MW');
    });
  });

  describe('formatLatency', () => {
    it('formats microseconds correctly', () => {
      expect(formatLatency(0.5)).toBe('500μs');
      expect(formatLatency(0.001)).toBe('1μs');
    });

    it('formats milliseconds correctly', () => {
      expect(formatLatency(1)).toBe('1.0ms');
      expect(formatLatency(50.5)).toBe('50.5ms');
      expect(formatLatency(999)).toBe('999.0ms');
    });

    it('formats seconds correctly', () => {
      expect(formatLatency(1000)).toBe('1.00s');
      expect(formatLatency(2500)).toBe('2.50s');
    });
  });

  describe('getActionColor', () => {
    it('returns correct colors for actions', () => {
      expect(getActionColor('maintain')).toBe('text-success-500');
      expect(getActionColor('reduce')).toBe('text-warning-500');
      expect(getActionColor('cutoff')).toBe('text-danger-500');
    });
  });

  describe('getPriorityLabel', () => {
    it('returns correct labels for priority tiers', () => {
      expect(getPriorityLabel(1)).toBe('Hospital');
      expect(getPriorityLabel(2)).toBe('Factory');
      expect(getPriorityLabel(3)).toBe('Residential');
    });
  });

  describe('calculatePercentage', () => {
    it('calculates percentage correctly', () => {
      expect(calculatePercentage(50, 100)).toBe(50);
      expect(calculatePercentage(25, 100)).toBe(25);
      expect(calculatePercentage(1, 3)).toBe(33);
    });

    it('handles zero total', () => {
      expect(calculatePercentage(50, 0)).toBe(0);
    });
  });
});