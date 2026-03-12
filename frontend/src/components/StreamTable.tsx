import React, { useEffect, useRef, useState } from 'react';
import type { StreamTableProps, AllocationResult } from '../types';

/**
 * Live stream table component for displaying recent allocation results
 * 
 * Features:
 * - Real-time updates with smooth fade-in animations
 * - Color-coded actions (maintain=green, reduce=yellow, cutoff=red)
 * - Auto-scroll to show latest entries
 * - Latency metrics display
 * - Configurable maximum rows
 * 
 * Requirements: 4.5, 12.3, 7.3
 */
export const StreamTable: React.FC<StreamTableProps> = ({
  allocations,
  maxRows = 12
}) => {
  const [displayAllocations, setDisplayAllocations] = useState<AllocationResult[]>([]);
  const [newEntryIds, setNewEntryIds] = useState<Set<string>>(new Set());
  const tableRef = useRef<HTMLDivElement>(null);
  const previousAllocationsRef = useRef<AllocationResult[]>([]);

  // Action color configurations
  const getActionColor = (action: AllocationResult['action']) => {
    switch (action) {
      case 'maintain':
        return {
          bg: 'bg-green-500/20',
          text: 'text-green-400',
          border: 'border-green-500/30',
          dot: 'bg-green-400'
        };
      case 'reduce':
        return {
          bg: 'bg-yellow-500/20',
          text: 'text-yellow-400',
          border: 'border-yellow-500/30',
          dot: 'bg-yellow-400'
        };
      case 'cutoff':
        return {
          bg: 'bg-red-500/20',
          text: 'text-red-400',
          border: 'border-red-500/30',
          dot: 'bg-red-400'
        };
      default:
        return {
          bg: 'bg-slate-500/20',
          text: 'text-slate-400',
          border: 'border-slate-500/30',
          dot: 'bg-slate-400'
        };
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return new Date().toLocaleTimeString();
    return new Date(timestamp).toLocaleTimeString();
  };

  // Format power value with units
  const formatPower = (power: number) => {
    if (power >= 1000) {
      return `${(power / 1000).toFixed(1)} MW`;
    }
    return `${power.toFixed(0)} kW`;
  };

  // Get latency color based on performance thresholds
  const getLatencyColor = (latency: number) => {
    if (latency > 10) return 'text-red-400';
    if (latency > 7) return 'text-yellow-400';
    return 'text-green-400';
  };

  // Update display allocations when new data arrives
  useEffect(() => {
    if (!allocations || allocations.length === 0) return;

    const previousIds = new Set(previousAllocationsRef.current.map(a => a.node_id));
    
    // Find new entries for animation
    const newIds = new Set<string>();
    allocations.forEach(allocation => {
      if (!previousIds.has(allocation.node_id)) {
        newIds.add(allocation.node_id);
      }
    });

    // Add timestamps to allocations if not present
    const timestampedAllocations = allocations.map(allocation => ({
      ...allocation,
      timestamp: allocation.timestamp || Date.now()
    }));

    // Sort by timestamp (newest first) and limit to maxRows
    const sortedAllocations = [...timestampedAllocations]
      .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
      .slice(0, maxRows);

    setDisplayAllocations(sortedAllocations);
    setNewEntryIds(newIds);
    previousAllocationsRef.current = allocations;

    // Clear new entry animation after delay
    if (newIds.size > 0) {
      const timer = setTimeout(() => {
        setNewEntryIds(new Set());
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [allocations, maxRows]);

  // Auto-scroll to top when new entries arrive
  useEffect(() => {
    if (newEntryIds.size > 0 && tableRef.current) {
      tableRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, [newEntryIds]);

  // Calculate average latency for display
  const averageLatency = displayAllocations.length > 0
    ? displayAllocations.reduce((sum, allocation) => sum + allocation.latency_ms, 0) / displayAllocations.length
    : 0;

  return (
    <div className="space-y-4">
      {/* Header with metrics */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">
          Live Allocation Stream
        </h3>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-slate-400">
              {displayAllocations.length} active
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Avg Latency:</span>
            <span className={`font-medium ${getLatencyColor(averageLatency)}`}>
              {averageLatency.toFixed(1)}ms
            </span>
          </div>
        </div>
      </div>

      {/* Table container with scroll */}
      <div 
        ref={tableRef}
        className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden"
      >
        <div className="max-h-80 overflow-y-auto scrollbar-thin scrollbar-track-slate-800 scrollbar-thumb-slate-600">
          {displayAllocations.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-slate-800 flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p>Waiting for allocation data...</p>
              <p className="text-sm mt-1">Real-time updates will appear here</p>
            </div>
          ) : (
            <table className="w-full">
              {/* Table header */}
              <thead className="bg-slate-800 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                    Node ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                    Power
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                    Latency
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>

              {/* Table body */}
              <tbody className="divide-y divide-slate-700">
                {displayAllocations.map((allocation, index) => {
                  const colors = getActionColor(allocation.action);
                  const isNew = newEntryIds.has(allocation.node_id);
                  
                  return (
                    <tr
                      key={`${allocation.node_id}-${allocation.timestamp || index}`}
                      className={`
                        transition-all duration-500 ease-out hover:bg-slate-800/50
                        ${isNew ? 'animate-fade-in bg-slate-800/30' : ''}
                      `}
                    >
                      {/* Node ID */}
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
                          <span className="text-white font-medium text-sm">
                            {allocation.node_id}
                          </span>
                        </div>
                      </td>

                      {/* Allocated Power */}
                      <td className="px-4 py-3">
                        <span className="text-slate-200 font-mono text-sm">
                          {formatPower(allocation.allocated_power)}
                        </span>
                      </td>

                      {/* Action */}
                      <td className="px-4 py-3">
                        <span className={`
                          inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${colors.bg} ${colors.text} ${colors.border} border
                        `}>
                          {allocation.action}
                        </span>
                      </td>

                      {/* Latency */}
                      <td className="px-4 py-3">
                        <span className={`font-mono text-sm ${getLatencyColor(allocation.latency_ms)}`}>
                          {allocation.latency_ms.toFixed(1)}ms
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td className="px-4 py-3">
                        <span className="text-slate-400 text-sm font-mono">
                          {formatTimestamp(allocation.timestamp)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Footer with summary stats */}
      <div className="flex items-center justify-between text-sm text-slate-400">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full" />
            <span>Maintain: {displayAllocations.filter(a => a.action === 'maintain').length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-yellow-400 rounded-full" />
            <span>Reduce: {displayAllocations.filter(a => a.action === 'reduce').length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-red-400 rounded-full" />
            <span>Cutoff: {displayAllocations.filter(a => a.action === 'cutoff').length}</span>
          </div>
        </div>
        <div>
          Showing {Math.min(displayAllocations.length, maxRows)} of {displayAllocations.length} entries
        </div>
      </div>
    </div>
  );
};

export default StreamTable;