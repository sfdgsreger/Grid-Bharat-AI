import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
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
  // Determine node color based on Tier logic
  const getNodeColor = () => {
    if (node.priority_tier === 1) {
      return 'bg-emerald-500'; // Emerald green
    }
    if (node.priority_tier === 2) {
      return allocation?.action === 'reduce' ? 'bg-amber-500' : 'bg-blue-500'; // Amber/Gold or solid Blue
    }
    if (node.priority_tier === 3) {
      if (allocation?.action === 'cutoff') return 'bg-red-500'; // Red cutoff
      if (!allocation || allocation.allocated_power === 0) return 'bg-slate-600'; // dimmed gray when inactive
      return 'bg-slate-500';
    }
    return 'bg-gray-500';
  };

  // Get priority tier label
  const getPriorityLabel = () => {
    if (node.node_id.toLowerCase().includes('icu')) return 'Hospital (ICU)';
    if (node.node_id.toLowerCase().includes('ventilator')) return 'Hospital (Ventilators)';
    if (node.node_id.toLowerCase().includes('hallway')) return 'Hospital (Hallways)';
    if (node.node_id.toLowerCase().includes('canteen')) return 'Hospital (Canteen)';

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
    if (!allocation) return 'text-gray-400';
    
    switch (allocation.action) {
      case 'maintain':
        return 'text-emerald-400';
      case 'reduce':
        return 'text-amber-400';
      case 'cutoff':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // Flow duration dynamic based on allocated power
  const flowDuration = useMemo(() => {
    if (!allocation || allocation.allocated_power === 0) return 0;
    // Faster flow = smaller duration value
    const power = allocation.allocated_power;
    return Math.max(0.2, 2 - (power / 500) * 1.5);
  }, [allocation]);

  // Calculate percentage breakdown for tooltips
  const sourceBreakdown = useMemo(() => {
    if (!allocation || !allocation.source_mix) return '';
    const total = Object.values(allocation.source_mix).reduce((sum, val) => sum + (val as number || 0), 0);
    if (total === 0) return '';
    
    return Object.entries(allocation.source_mix)
      .map(([source, amount]) => {
        const percentage = Math.round(((amount as number) / total) * 100);
        return `${source.charAt(0).toUpperCase() + source.slice(1)}: ${percentage}%`;
      })
      .join(', ');
  }, [allocation]);

  return (
    <>
      {/* Connection line */}
      <svg 
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 1 }}
      >
        <path
          d={connectionPath}
          stroke="currentColor"
          fill="none"
          className={`${getConnectionColor()} opacity-30`}
          strokeWidth="2"
          strokeDasharray={allocation?.action === 'cutoff' ? '5,5' : 'none'}
        />
        {/* Animated Flow Dashing Lines */}
        {flowDuration > 0 && allocation?.action !== 'cutoff' && (
          <motion.path
            d={connectionPath}
            stroke="currentColor"
            fill="none"
            className={`${getConnectionColor()} opacity-80`}
            strokeWidth="3"
            strokeDasharray="10 15"
            initial={{ strokeDashoffset: 100 }}
            animate={{ strokeDashoffset: 0 }}
            transition={{
              duration: flowDuration,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        )}
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
        {/* Floating kW label */}
        {allocation && allocation.allocated_power > 0 && (
          <div className="absolute -top-7 left-1/2 transform -translate-x-1/2 whitespace-nowrap z-10 hidden md:block">
            <span className="bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded text-[10px] font-bold text-white shadow-sm shadow-black/50">
              {Math.round(allocation.allocated_power)} kW
            </span>
          </div>
        )}

        {/* Node circle */}
        <div className="relative">
          {/* Heartbeat pulse effect for Tier 1 */}
          {node.priority_tier === 1 && (
            <div className={`absolute inset-0 rounded-full animate-ping opacity-75 ${getNodeColor()}`} />
          )}

          <div
            className={`
              relative w-12 h-12 rounded-full ${getNodeColor()} 
              border-2 border-white shadow-lg
              transition-all duration-300 ease-in-out
              group-hover:scale-110 group-hover:shadow-xl
              flex items-center justify-center
              ${node.priority_tier === 3 && allocation?.action === 'cutoff' ? 'opacity-90 grayscale' : ''}
            `}
          >
            {/* Priority tier indicator */}
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center text-xs font-bold text-gray-800">
              {node.priority_tier}
            </div>
          </div>
        </div>

        {/* Node Name Label */}
        <div className="absolute top-14 left-1/2 transform -translate-x-1/2 whitespace-nowrap text-[11px] font-semibold text-slate-300 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50 shadow-sm pointer-events-none">
          {node.node_id.split('_').map((word, i, arr) => {
            if (i === arr.length - 1 && ['icu', 'ventilators', 'hallways', 'canteen'].includes(word.toLowerCase())) {
              return `[${word.toUpperCase()}]`;
            }
            return word.charAt(0).toUpperCase() + word.slice(1);
          }).join(' ')}
        </div>

        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20">
          <div className="bg-gray-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-2 shadow-xl min-w-max">
            <div className="font-semibold text-emerald-100">{getPriorityLabel()}</div>
            <div className="text-gray-300 mt-0.5">ID: {node.node_id}</div>
            <div className="text-gray-300">Load: {Math.round(node.current_load)}kW</div>
            
            {allocation && (
              <>
                <div className="border-t border-gray-700 mt-1 pt-1">
                  <div className="text-gray-200">
                    Allocated: <span className="font-bold">{Math.round(allocation.allocated_power)}kW</span>
                  </div>
                  {sourceBreakdown && (
                    <div className="text-[10px] font-medium text-emerald-400 mt-1">
                      Mix: {sourceBreakdown}
                    </div>
                  )}
                  <div className={`font-bold mt-1 ${
                    allocation.action === 'maintain' ? 'text-green-400' :
                    allocation.action === 'reduce' ? 'text-amber-400' :
                    'text-red-400'
                  }`}>
                    Action: {allocation.action.toUpperCase()}
                  </div>
                  <div className="text-gray-500 text-[10px] mt-0.5 font-mono">
                    Latency: {allocation.latency_ms.toFixed(1)}ms
                  </div>
                </div>
              </>
            )}
            {!allocation && (
              <div className="text-gray-400 text-xs italic mt-1 pt-1 border-t border-gray-700">No active allocation</div>
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