import { describe, it, expect } from 'vitest';
import { formatDate, formatTime, getStatusColor, truncate } from './utils';

describe('formatDate', () => {
  it('formats a date string into a locale date', () => {
    expect(formatDate('2024-01-15T00:00:00Z')).toBe(new Date('2024-01-15T00:00:00Z').toLocaleDateString());
  });
});

describe('formatTime', () => {
  it('formats a date into a locale time', () => {
    const date = new Date('2024-01-15T10:30:00Z');
    expect(formatTime(date)).toBe(date.toLocaleTimeString());
  });
});

describe('getStatusColor', () => {
  it('maps success-like statuses to emerald', () => {
    expect(getStatusColor('completed')).toBe('text-emerald-400');
    expect(getStatusColor('ACTIVE')).toBe('text-emerald-400');
  });

  it('maps failure-like statuses to red', () => {
    expect(getStatusColor('failed')).toBe('text-red-400');
    expect(getStatusColor('error')).toBe('text-red-400');
  });

  it('falls back to zinc for unknown statuses', () => {
    expect(getStatusColor('queued')).toBe('text-zinc-400');
  });
});

describe('truncate', () => {
  it('leaves short strings unchanged', () => {
    expect(truncate('hello', 10)).toBe('hello');
  });

  it('truncates long strings and appends an ellipsis', () => {
    expect(truncate('hello world', 5)).toBe('hello...');
  });
});
