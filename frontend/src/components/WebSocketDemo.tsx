import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

/**
 * Demo component showing WebSocket hook usage
 * Displays real-time allocation data and connection status
 */
export const WebSocketDemo: React.FC = () => {
  const { data, state, connect, disconnect } = useWebSocket();

  const getStatusColor = () => {
    if (state.isConnected) return 'text-green-500';
    if (state.isConnecting) return 'text-yellow-500';
    if (state.error) return 'text-red-500';
    return 'text-gray-500';
  };

  const getStatusText = () => {
    if (state.isConnected) return 'Connected';
    if (state.isConnecting) return 'Connecting...';
    if (state.error) return `Error: ${state.error}`;
    return 'Disconnected';
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">WebSocket Connection Status</h2>
        
        {/* Connection Status */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${state.isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className={`font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
          
          <div className="space-x-2">
            <button
              onClick={connect}
              disabled={state.isConnecting}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              Connect
            </button>
            <button
              onClick={disconnect}
              disabled={!state.isConnected}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm text-gray-600">Latency</div>
            <div className="text-2xl font-bold text-blue-600">
              {data.latency.toFixed(1)}ms
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm text-gray-600">Allocations</div>
            <div className="text-2xl font-bold text-green-600">
              {data.allocations.length}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm text-gray-600">Reconnect Attempts</div>
            <div className="text-2xl font-bold text-yellow-600">
              {state.reconnectAttempts}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Allocations */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Recent Allocations</h3>
        
        {data.allocations.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No allocation data received yet
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Node ID</th>
                  <th className="text-left py-2">Power (kW)</th>
                  <th className="text-left py-2">Action</th>
                  <th className="text-left py-2">Latency (ms)</th>
                  <th className="text-left py-2">Source Mix</th>
                </tr>
              </thead>
              <tbody>
                {data.allocations.slice(0, 10).map((allocation, index) => (
                  <tr key={`${allocation.node_id}-${index}`} className="border-b">
                    <td className="py-2 font-mono text-xs">{allocation.node_id}</td>
                    <td className="py-2">{allocation.allocated_power.toFixed(1)}</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs text-white ${
                        allocation.action === 'maintain' ? 'bg-green-500' :
                        allocation.action === 'reduce' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}>
                        {allocation.action}
                      </span>
                    </td>
                    <td className="py-2">{allocation.latency_ms.toFixed(1)}</td>
                    <td className="py-2 text-xs">
                      {Object.entries(allocation.source_mix)
                        .filter(([_, value]) => value && value > 0)
                        .map(([source, value]) => `${source}: ${value}kW`)
                        .join(', ') || 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default WebSocketDemo;