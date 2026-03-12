import React, { useMemo } from 'react';
import type { EnergyNode, AllocationResult, PowerMapProps } from '../types';

interface NodePosition {
  x: number;
  y: number;
}

interface NodeConnectionProps {
  node: EnergyNode;
  allocation: AllocationResult | undefined;
  position: NodePosition;
  centerPosition: NodePosition;
}

/**
 * Individual node component with connection line to central hub
 */
const NodeConnection: React.FC<NodeConnectionProps> = ({ 
  node, 
  allocation, 
  position, 
  centerPosition 
}) => {
  // Determine node color based on allocation action
  const getNodeColor = () => {
    if (!allocation) return 'bg-gray-500';
    
    switch (allocation.action) {
      case 'maintain':
        return 'bg-green-500';
      case 'reduce':
        return 'bg-yellow-500';
      case 'cutoff':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get priority tier label
  const getPriorityLabel = () => {
    switch (node.priority_tier) {
      case 1:
        return 'Hospital';
      case 2:
        return 'Factory';
      case 3:
        return 'Residential';
      default:
        return 'Unknown';
    }
  };

  // Calculate connection line path
  const connectionPath = `M ${centerPosition.x} ${centerPosition.y} L ${position.x} ${position.y}`;

  // Get connection line color based on allocation status
  const getConnectionColor = () => {
    if (!allocation) return 'stroke-gray-400';
    
    switch (allocation.action) {
      case 'maintain':
        return 'stroke-green-400';
      case 'reduce':
        return 'stroke-yellow-400';
      case 'cutoff':
        return 'stroke-red-400';
      default:
        return 'stroke-gray-400';
    }
  };

  return (
    <>
      {/* Connection line */}
      <svg 
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 1 }}
      >
        <path
          d={connectionPath}
          className={`${getConnectionColor()} opacity-60`}
          strokeWidth="2"
          strokeDasharray={allocation?.action === 'cutoff' ? '5,5' : 'none'}
        />
      </svg>

      {/* Node */}
      <div
        className="absolute transform -translate-x-1/2 -translate-y-1/2 group cursor-pointer"
        style={{ 
          left: position.x, 
          top: position.y,
          zIndex: 2
        }}
      >
        {/* Node circle */}
        <div
          className={`
            w-12 h-12 rounded-full ${getNodeColor()} 
            border-2 border-white shadow-lg
            transition-all duration-300 ease-in-out
            group-hover:scale-110 group-hover:shadow-xl
            ${allocation?.action === 'cutoff' ? 'animate-pulse' : ''}
          `}
        >
          {/* Priority tier indicator */}
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center text-xs font-bold text-gray-800">
            {node.priority_tier}
          </div>
        </div>

        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg min-w-max">
            <div className="font-semibold">{getPriorityLabel()}</div>
            <div className="text-gray-300">ID: {node.node_id}</div>
            <div className="text-gray-300">Load: {node.current_load}kW</div>
            <div className="text-gray-300">Source: {node.source_type}</div>
            {allocation && (
              <>
                <div className="border-t border-gray-700 mt-1 pt-1">
                  <div className="text-gray-300">
                    Allocated: {allocation.allocated_power}kW
                  </div>
                  <div className={`font-semibold ${
                    allocation.action === 'maintain' ? 'text-green-400' :
                    allocation.action === 'reduce' ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>
                    Action: {allocation.action.toUpperCase()}
                  </div>
                  <div className="text-gray-300 text-xs">
                    Latency: {allocation.latency_ms}ms
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

/**
 * Power Connection Map Component
 * 
 * Interactive visualization showing energy nodes connected to a central hub
 * with real-time status updates based on allocation actions.
 * 
 * Requirements: 12.1, 12.5, 12.6, 12.7, 12.8
 */
export const PowerMap: React.FC<PowerMapProps> = ({ nodes, allocations }) => {
  // Calculate node positions in a circular layout around the center
  const nodePositions = useMemo(() => {
    const positions: Record<string, NodePosition> = {};
    const centerX = 300; // Half of container width (600px)
    const centerY = 200; // Half of container height (400px)
    const radius = 140; // Distance from center
    
    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI;
      positions[node.node_id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });
    
    return positions;
  }, [nodes]);

  const centerPosition: NodePosition = { x: 300, y: 200 };

  // Create allocation lookup for quick access
  const allocationMap = useMemo(() => {
    const map: Record<string, AllocationResult> = {};
    allocations.forEach(allocation => {
      map[allocation.node_id] = allocation;
    });
    return map;
  }, [allocations]);

  // Calculate summary statistics
  const stats = useMemo(() => {
    const totalNodes = nodes.length;
    const activeAllocations = allocations.length;
    const maintainCount = allocations.filter(a => a.action === 'maintain').length;
    const reduceCount = allocations.filter(a => a.action === 'reduce').length;
    const cutoffCount = allocations.filter(a => a.action === 'cutoff').length;
    
    return {
      totalNodes,
      activeAllocations,
      maintainCount,
      reduceCount,
      cutoffCount,
    };
  }, [nodes, allocations]);

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Power Connection Map</h2>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-300">Maintain ({stats.maintainCount})</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span className="text-gray-300">Reduce ({stats.reduceCount})</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-gray-300">Cutoff ({stats.cutoffCount})</span>
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div className="relative w-full h-96 bg-slate-900 rounded-lg overflow-hidden">
        {/* Grid background */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full">
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="white" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        {/* Central Hub */}
        <div
          className="absolute transform -translate-x-1/2 -translate-y-1/2"
          style={{ 
            left: centerPosition.x, 
            top: centerPosition.y,
            zIndex: 3
          }}
        >
          <div className="relative">
            {/* Hub circle with pulsing animation */}
            <div className="w-16 h-16 bg-blue-500 rounded-full animate-pulse border-4 border-white shadow-xl">
              <div className="absolute inset-2 bg-blue-400 rounded-full animate-ping"></div>
            </div>
            
            {/* Hub label */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2">
              <div className="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded">
                Grid Hub
              </div>
            </div>
          </div>
        </div>

        {/* Nodes and connections */}
        {nodes.map((node) => (
          <NodeConnection
            key={node.node_id}
            node={node}
            allocation={allocationMap[node.node_id]}
            position={nodePositions[node.node_id]}
            centerPosition={centerPosition}
          />
        ))}

        {/* No data message */}
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-gray-400 text-center">
              <div className="text-lg font-medium mb-2">No Energy Nodes</div>
              <div className="text-sm">Waiting for real-time data...</div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 flex justify-between items-center text-sm text-gray-400">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Priority 1 (Hospital)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Priority 2 (Factory)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Priority 3 (Residential)</span>
          </div>
        </div>
        <div className="text-right">
          <div>Total Nodes: {stats.totalNodes}</div>
          <div>Active Allocations: {stats.activeAllocations}</div>
        </div>
      </div>
    </div>
  );
};

export default PowerMap;