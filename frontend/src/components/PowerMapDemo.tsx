import React, { useState, useEffect } from 'react';
import PowerMap from './PowerMap';
import type { EnergyNode, AllocationResult } from '../types';

/**
 * Demo component to showcase PowerMap functionality
 * Simulates real-time updates with changing allocation statuses
 */
export const PowerMapDemo: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(Date.now());

  // Sample nodes representing different types of energy consumers
  const nodes: EnergyNode[] = [
    {
      node_id: 'hospital_001',
      current_load: 150,
      priority_tier: 1,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6139, lng: 77.2090 },
      timestamp: currentTime,
    },
    {
      node_id: 'hospital_002',
      current_load: 200,
      priority_tier: 1,
      source_type: 'Diesel',
      status: 'active',
      location: { lat: 28.6180, lng: 77.2120 },
      timestamp: currentTime,
    },
    {
      node_id: 'factory_001',
      current_load: 300,
      priority_tier: 2,
      source_type: 'Solar',
      status: 'active',
      location: { lat: 28.6200, lng: 77.2100 },
      timestamp: currentTime,
    },
    {
      node_id: 'factory_002',
      current_load: 250,
      priority_tier: 2,
      source_type: 'Grid',
      status: 'degraded',
      location: { lat: 28.6080, lng: 77.2080 },
      timestamp: currentTime,
    },
    {
      node_id: 'residential_001',
      current_load: 75,
      priority_tier: 3,
      source_type: 'Battery',
      status: 'active',
      location: { lat: 28.6100, lng: 77.2050 },
      timestamp: currentTime,
    },
    {
      node_id: 'residential_002',
      current_load: 50,
      priority_tier: 3,
      source_type: 'Solar',
      status: 'active',
      location: { lat: 28.6160, lng: 77.2110 },
      timestamp: currentTime,
    },
    {
      node_id: 'residential_003',
      current_load: 60,
      priority_tier: 3,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6120, lng: 77.2070 },
      timestamp: currentTime,
    },
    {
      node_id: 'factory_003',
      current_load: 180,
      priority_tier: 2,
      source_type: 'Battery',
      status: 'active',
      location: { lat: 28.6140, lng: 77.2130 },
      timestamp: currentTime,
    },
  ];

  // Simulate dynamic allocation results that change over time
  const [allocations, setAllocations] = useState<AllocationResult[]>([]);

  useEffect(() => {
    const updateAllocations = () => {
      const time = Date.now();
      const cycle = Math.floor(time / 3000) % 3; // 3-second cycles
      
      let newAllocations: AllocationResult[];
      
      switch (cycle) {
        case 0: // Normal operation - all nodes maintained
          newAllocations = [
            {
              node_id: 'hospital_001',
              allocated_power: 150,
              source_mix: { grid: 150 },
              action: 'maintain',
              latency_ms: 5,
            },
            {
              node_id: 'hospital_002',
              allocated_power: 200,
              source_mix: { diesel: 200 },
              action: 'maintain',
              latency_ms: 6,
            },
            {
              node_id: 'factory_001',
              allocated_power: 300,
              source_mix: { solar: 300 },
              action: 'maintain',
              latency_ms: 7,
            },
            {
              node_id: 'factory_002',
              allocated_power: 250,
              source_mix: { grid: 250 },
              action: 'maintain',
              latency_ms: 8,
            },
            {
              node_id: 'residential_001',
              allocated_power: 75,
              source_mix: { battery: 75 },
              action: 'maintain',
              latency_ms: 3,
            },
            {
              node_id: 'residential_002',
              allocated_power: 50,
              source_mix: { solar: 50 },
              action: 'maintain',
              latency_ms: 4,
            },
            {
              node_id: 'residential_003',
              allocated_power: 60,
              source_mix: { grid: 60 },
              action: 'maintain',
              latency_ms: 4,
            },
            {
              node_id: 'factory_003',
              allocated_power: 180,
              source_mix: { battery: 180 },
              action: 'maintain',
              latency_ms: 7,
            },
          ];
          break;
          
        case 1: // Moderate shortage - some reductions
          newAllocations = [
            {
              node_id: 'hospital_001',
              allocated_power: 150,
              source_mix: { grid: 150 },
              action: 'maintain',
              latency_ms: 5,
            },
            {
              node_id: 'hospital_002',
              allocated_power: 200,
              source_mix: { diesel: 200 },
              action: 'maintain',
              latency_ms: 6,
            },
            {
              node_id: 'factory_001',
              allocated_power: 250,
              source_mix: { solar: 250 },
              action: 'reduce',
              latency_ms: 7,
            },
            {
              node_id: 'factory_002',
              allocated_power: 200,
              source_mix: { grid: 200 },
              action: 'reduce',
              latency_ms: 8,
            },
            {
              node_id: 'residential_001',
              allocated_power: 50,
              source_mix: { battery: 50 },
              action: 'reduce',
              latency_ms: 3,
            },
            {
              node_id: 'residential_002',
              allocated_power: 30,
              source_mix: { solar: 30 },
              action: 'reduce',
              latency_ms: 4,
            },
            {
              node_id: 'residential_003',
              allocated_power: 40,
              source_mix: { grid: 40 },
              action: 'reduce',
              latency_ms: 4,
            },
            {
              node_id: 'factory_003',
              allocated_power: 150,
              source_mix: { battery: 150 },
              action: 'reduce',
              latency_ms: 7,
            },
          ];
          break;
          
        case 2: // Severe shortage - cutoffs for lowest priority
          newAllocations = [
            {
              node_id: 'hospital_001',
              allocated_power: 150,
              source_mix: { grid: 150 },
              action: 'maintain',
              latency_ms: 5,
            },
            {
              node_id: 'hospital_002',
              allocated_power: 200,
              source_mix: { diesel: 200 },
              action: 'maintain',
              latency_ms: 6,
            },
            {
              node_id: 'factory_001',
              allocated_power: 200,
              source_mix: { solar: 200 },
              action: 'reduce',
              latency_ms: 7,
            },
            {
              node_id: 'factory_002',
              allocated_power: 150,
              source_mix: { grid: 150 },
              action: 'reduce',
              latency_ms: 8,
            },
            {
              node_id: 'residential_001',
              allocated_power: 0,
              source_mix: {},
              action: 'cutoff',
              latency_ms: 3,
            },
            {
              node_id: 'residential_002',
              allocated_power: 0,
              source_mix: {},
              action: 'cutoff',
              latency_ms: 4,
            },
            {
              node_id: 'residential_003',
              allocated_power: 0,
              source_mix: {},
              action: 'cutoff',
              latency_ms: 4,
            },
            {
              node_id: 'factory_003',
              allocated_power: 100,
              source_mix: { battery: 100 },
              action: 'reduce',
              latency_ms: 7,
            },
          ];
          break;
          
        default:
          newAllocations = [];
      }
      
      setAllocations(newAllocations);
      setCurrentTime(time);
    };

    // Initial update
    updateAllocations();
    
    // Update every 500ms for smooth transitions
    const interval = setInterval(updateAllocations, 500);
    
    return () => clearInterval(interval);
  }, []);

  const getScenarioDescription = () => {
    const cycle = Math.floor(currentTime / 3000) % 3;
    switch (cycle) {
      case 0:
        return "Normal Operation - All nodes receiving full power";
      case 1:
        return "Moderate Shortage - Factories and residential areas reduced";
      case 2:
        return "Severe Shortage - Residential areas cut off, hospitals maintained";
      default:
        return "Initializing...";
    }
  };

  return (
    <div className="space-y-6">
      {/* Scenario Status */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">
              Live Simulation Demo
            </h3>
            <p className="text-slate-300 text-sm">
              {getScenarioDescription()}
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">Cycle Updates Every 3s</div>
            <div className="text-xs text-slate-500">
              Last Update: {new Date(currentTime).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Power Map */}
      <PowerMap nodes={nodes} allocations={allocations} />
      
      {/* Instructions */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h4 className="text-md font-semibold text-white mb-2">
          Interactive Features
        </h4>
        <ul className="text-sm text-slate-300 space-y-1">
          <li>• Hover over nodes to see detailed information</li>
          <li>• Watch connection lines change color based on allocation status</li>
          <li>• Observe priority-based allocation during shortages</li>
          <li>• Notice how hospitals (Priority 1) are always maintained</li>
          <li>• See how residential areas (Priority 3) are cut off first</li>
        </ul>
      </div>
    </div>
  );
};

export default PowerMapDemo;