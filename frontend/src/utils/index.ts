import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format power values with appropriate units
 */
export function formatPower(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}MW`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}kW`;
  } else {
    return `${value.toFixed(0)}W`;
  }
}

/**
 * Format latency values
 */
export function formatLatency(ms: number): string {
  if (ms < 1) {
    return `${(ms * 1000).toFixed(0)}μs`;
  } else if (ms < 1000) {
    return `${ms.toFixed(1)}ms`;
  } else {
    return `${(ms / 1000).toFixed(2)}s`;
  }
}

/**
 * Get color class based on allocation action
 */
export function getActionColor(action: 'maintain' | 'reduce' | 'cutoff'): string {
  switch (action) {
    case 'maintain':
      return 'text-success-500';
    case 'reduce':
      return 'text-warning-500';
    case 'cutoff':
      return 'text-danger-500';
    default:
      return 'text-slate-400';
  }
}

/**
 * Get priority tier label
 */
export function getPriorityLabel(tier: 1 | 2 | 3): string {
  switch (tier) {
    case 1:
      return 'Hospital';
    case 2:
      return 'Factory';
    case 3:
      return 'Residential';
    default:
      return 'Unknown';
  }
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((value / total) * 100);
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}