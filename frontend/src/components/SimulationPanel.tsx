import React, { useState } from 'react';
import { API_BASE_URL, API_ENDPOINTS } from '../constants';
import type { SimulationPanelProps } from '../types';

interface SimulationResult {
  status: string;
  reduction: number;
  timestamp: number;
}

interface SimulationState {
  status: 'idle' | 'running' | 'completed' | 'error';
  result: SimulationResult | null;
  error: string | null;
}

const SimulationPanel: React.FC<SimulationPanelProps> = ({ onSimulate, isSimulating }) => {
  const [failurePercentage, setFailurePercentage] = useState(25);
  const [simulationState, setSimulationState] = useState<SimulationState>({
    status: 'idle',
    result: null,
    error: null
  });

  const handleSimulate = async () => {
    if (isSimulating) return;

    setSimulationState({
      status: 'running',
      result: null,
      error: null
    });

    try {
      // Call the API endpoint directly
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.SIMULATE_FAILURE}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          failure_percentage: failurePercentage / 100 // Convert percentage to decimal
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: SimulationResult = await response.json();
      
      setSimulationState({
        status: 'completed',
        result,
        error: null
      });

      // Call the parent callback
      onSimulate(failurePercentage);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setSimulationState({
        status: 'error',
        result: null,
        error: errorMessage
      });
    }
  };

  const getStatusColor = () => {
    switch (simulationState.status) {
      case 'running':
        return 'text-yellow-400';
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const getStatusText = () => {
    switch (simulationState.status) {
      case 'running':
        return 'Simulation in progress...';
      case 'completed':
        return 'Simulation completed successfully';
      case 'error':
        return 'Simulation failed';
      default:
        return 'Ready to simulate';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Grid Failure Simulation</h2>
        <div className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </div>
      </div>

      {/* Failure Percentage Control */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-slate-300">
            Failure Percentage
          </label>
          <div className="text-lg font-bold text-white">
            {failurePercentage}%
          </div>
        </div>
        
        {/* Slider */}
        <div className="relative">
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={failurePercentage}
            onChange={(e) => setFailurePercentage(Number(e.target.value))}
            disabled={isSimulating || simulationState.status === 'running'}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
          />
          
          {/* Slider track markers */}
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>0%</span>
            <span>25%</span>
            <span>50%</span>
            <span>75%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Percentage Input */}
        <div className="flex items-center space-x-4">
          <label className="text-sm text-slate-400">Precise value:</label>
          <input
            type="number"
            min="0"
            max="100"
            value={failurePercentage}
            onChange={(e) => setFailurePercentage(Math.max(0, Math.min(100, Number(e.target.value))))}
            disabled={isSimulating || simulationState.status === 'running'}
            className="w-20 px-3 py-1 bg-slate-700 border border-slate-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <span className="text-sm text-slate-400">%</span>
        </div>
      </div>

      {/* Trigger Button */}
      <button
        onClick={handleSimulate}
        disabled={isSimulating || simulationState.status === 'running'}
        className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
          isSimulating || simulationState.status === 'running'
            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
            : 'bg-red-600 hover:bg-red-700 text-white shadow-lg hover:shadow-xl transform hover:scale-[1.02]'
        }`}
      >
        {simulationState.status === 'running' ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>Simulating Grid Failure...</span>
          </div>
        ) : (
          `Simulate ${failurePercentage}% Grid Failure`
        )}
      </button>

      {/* Results Display */}
      {simulationState.result && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h3 className="text-lg font-semibold text-green-400 mb-3">Simulation Results</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Status:</span>
              <span className="ml-2 text-white font-medium capitalize">
                {simulationState.result.status}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Reduction:</span>
              <span className="ml-2 text-white font-medium">
                {(simulationState.result.reduction * 100).toFixed(1)}%
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-slate-400">Timestamp:</span>
              <span className="ml-2 text-white font-medium">
                {formatTimestamp(simulationState.result.timestamp)}
              </span>
            </div>
          </div>
          
          {/* Impact Summary */}
          <div className="mt-4 p-3 bg-slate-900 rounded-md">
            <h4 className="text-sm font-medium text-slate-300 mb-2">Impact Summary</h4>
            <p className="text-xs text-slate-400">
              Grid supply reduced by {(simulationState.result.reduction * 100).toFixed(1)}%. 
              Priority allocation algorithm will redistribute power to maintain critical infrastructure.
              Monitor the power map and stream table for real-time allocation updates.
            </p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {simulationState.error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-400 mb-2">Simulation Error</h3>
          <p className="text-sm text-red-300">{simulationState.error}</p>
          <button
            onClick={() => setSimulationState({ status: 'idle', result: null, error: null })}
            className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md transition-colors"
          >
            Clear Error
          </button>
        </div>
      )}

      {/* Information Panel */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-400 mb-2">How It Works</h3>
        <ul className="text-xs text-blue-300 space-y-1">
          <li>• Simulates grid failure by reducing total power supply</li>
          <li>• Triggers priority-based allocation algorithm</li>
          <li>• Hospitals (Tier 1) get power first, then factories (Tier 2), then residential (Tier 3)</li>
          <li>• Real-time updates appear in the power map and allocation table</li>
          <li>• Use different percentages to test various failure scenarios</li>
        </ul>
      </div>
    </div>
  );
};

export default SimulationPanel;