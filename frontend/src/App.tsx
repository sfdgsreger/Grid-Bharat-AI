import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import WebSocketDemo from './components/WebSocketDemo'
import PowerMap from './components/PowerMap'
import LiveGauge from './components/LiveGauge'
import StreamTable from './components/StreamTable'
import SimulationPanel from './components/SimulationPanel'
import PriorityController from './components/PriorityController'
import EnergyGraph from './components/EnergyGraph'
import { useWebSocket } from './hooks/useWebSocket'
import type { EnergyNode, AllocationResult } from './types'

function App() {
  // WebSocket connection for real-time data
  const { data: wsData, state: wsState } = useWebSocket();
  const [showDemo, setShowDemo] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isGridDown, setIsGridDown] = useState(false);

  // Handle grid failure simulation
  const handleGridToggle = () => {
    setIsGridDown(!isGridDown);
    
    // Show toast notification
    if (!isGridDown) {
      // Simulate grid failure
      console.log('🚨 Grid Failure Detected! Pathway AI rerouting power to Tier 1 nodes in 8.4ms.');
      // You can replace this with a proper toast library like react-hot-toast
      alert('🚨 Grid Failure Detected! Pathway AI rerouting power to Tier 1 nodes in 8.4ms.');
    } else {
      // Grid restored
      console.log('✅ Grid Restored! All systems operational.');
      alert('✅ Grid Restored! All systems operational.');
    }
  };

  // Handle simulation trigger
  const handleSimulate = (percentage: number) => {
    console.log(`Simulating ${percentage}% grid failure`);
    setIsSimulating(true);
    if (percentage > 0) {
      setIsGridDown(true);
    } else {
      setIsGridDown(false);
    }
    // Reset simulation state after a delay to allow for backend processing
    setTimeout(() => {
      setIsSimulating(false);
    }, 2000);
  };

  // Sample data for demonstration when no real data is available
  const sampleNodes: EnergyNode[] = [
    {
      node_id: 'hospital_001_icu',
      current_load: 60,
      priority_tier: 1,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6139, lng: 77.2090 },
      timestamp: Date.now(),
    },
    {
      node_id: 'hospital_001_ventilators',
      current_load: 30,
      priority_tier: 1,
      source_type: 'Battery',
      status: 'active',
      location: { lat: 28.6141, lng: 77.2085 },
      timestamp: Date.now(),
    },
    {
      node_id: 'hospital_001_hallways',
      current_load: 40,
      priority_tier: 3,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6135, lng: 77.2095 },
      timestamp: Date.now(),
    },
    {
      node_id: 'factory_001',
      current_load: 300,
      priority_tier: 2,
      source_type: 'Solar',
      status: 'active',
      location: { lat: 28.6200, lng: 77.2100 },
      timestamp: Date.now(),
    },
    {
      node_id: 'residential_001',
      current_load: 75,
      priority_tier: 3,
      source_type: 'Battery',
      status: 'active',
      location: { lat: 28.6100, lng: 77.2050 },
      timestamp: Date.now(),
    },
    {
      node_id: 'hospital_001_canteen',
      current_load: 20,
      priority_tier: 3,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6137, lng: 77.2092 },
      timestamp: Date.now(),
    },
    {
      node_id: 'factory_002',
      current_load: 250,
      priority_tier: 2,
      source_type: 'Grid',
      status: 'degraded',
      location: { lat: 28.6080, lng: 77.2080 },
      timestamp: Date.now(),
    },
    {
      node_id: 'residential_002',
      current_load: 50,
      priority_tier: 3,
      source_type: 'Solar',
      status: 'active',
      location: { lat: 28.6160, lng: 77.2110 },
      timestamp: Date.now(),
    },
  ];

  // Sample allocation results for demonstration
  const sampleAllocations: AllocationResult[] = [
    {
      node_id: 'hospital_001_icu',
      allocated_power: 60,
      source_mix: { grid: 60 },
      action: 'maintain',
      latency_ms: 5,
    },
    {
      node_id: 'hospital_001_ventilators',
      allocated_power: 30,
      source_mix: { battery: 30 },
      action: 'maintain',
      latency_ms: 4,
    },
    {
      node_id: 'hospital_001_hallways',
      allocated_power: 0,
      source_mix: {},
      action: 'cutoff',
      latency_ms: 3,
    },
    {
      node_id: 'factory_001',
      allocated_power: 250,
      source_mix: { solar: 250 },
      action: 'reduce',
      latency_ms: 7,
    },
    {
      node_id: 'residential_001',
      allocated_power: 0,
      source_mix: {},
      action: 'cutoff',
      latency_ms: 3,
    },
    {
      node_id: 'hospital_001_canteen',
      allocated_power: 0,
      source_mix: {},
      action: 'cutoff',
      latency_ms: 2,
    },
    {
      node_id: 'factory_002',
      allocated_power: 200,
      source_mix: { grid: 200 },
      action: 'reduce',
      latency_ms: 8,
    },
    {
      node_id: 'residential_002',
      allocated_power: 25,
      source_mix: { solar: 25 },
      action: 'reduce',
      latency_ms: 4,
    },
  ];

  // Demo Allocations state
  const [demoAllocations, setDemoAllocations] = useState<AllocationResult[]>(sampleAllocations);
  const [demoTime, setDemoTime] = useState(Date.now());

  useEffect(() => {
    // Only halt the demo loop if we're actually receiving real data stream
    const hasRealData = wsState.isConnected && wsData.allocations && wsData.allocations.length > 0;
    if (!showDemo || hasRealData) return;
    
    const updateAllocations = () => {
      const time = Date.now();
      const cycle = Math.floor(time / 3000) % 3; // 3-second cycles
      
      let newAllocations: AllocationResult[];
      
      switch (cycle) {
        case 0: // Normal operation
          newAllocations = [
            { node_id: 'hospital_001_icu', allocated_power: 60, source_mix: { grid: 60 }, action: 'maintain', latency_ms: 5 },
            { node_id: 'hospital_001_ventilators', allocated_power: 30, source_mix: { battery: 30 }, action: 'maintain', latency_ms: 4 },
            { node_id: 'hospital_001_hallways', allocated_power: 40, source_mix: { grid: 40 }, action: 'maintain', latency_ms: 3 },
            { node_id: 'hospital_001_canteen', allocated_power: 20, source_mix: { grid: 20 }, action: 'maintain', latency_ms: 3 },
            { node_id: 'factory_001', allocated_power: 300, source_mix: { solar: 300 }, action: 'maintain', latency_ms: 7 },
            { node_id: 'factory_002', allocated_power: 250, source_mix: { grid: 250 }, action: 'maintain', latency_ms: 8 },
            { node_id: 'residential_001', allocated_power: 75, source_mix: { battery: 75 }, action: 'maintain', latency_ms: 3 },
            { node_id: 'residential_002', allocated_power: 50, source_mix: { solar: 50 }, action: 'maintain', latency_ms: 4 },
          ];
          break;
        case 1: // Moderate shortage
          newAllocations = [
            { node_id: 'hospital_001_icu', allocated_power: 60, source_mix: { grid: 60 }, action: 'maintain', latency_ms: 5 },
            { node_id: 'hospital_001_ventilators', allocated_power: 30, source_mix: { battery: 30 }, action: 'maintain', latency_ms: 4 },
            { node_id: 'hospital_001_hallways', allocated_power: 20, source_mix: { grid: 20 }, action: 'reduce', latency_ms: 3 },
            { node_id: 'hospital_001_canteen', allocated_power: 0, source_mix: {}, action: 'cutoff', latency_ms: 3 },
            { node_id: 'factory_001', allocated_power: 250, source_mix: { solar: 250 }, action: 'reduce', latency_ms: 7 },
            { node_id: 'factory_002', allocated_power: 200, source_mix: { grid: 200 }, action: 'reduce', latency_ms: 8 },
            { node_id: 'residential_001', allocated_power: 50, source_mix: { battery: 50 }, action: 'reduce', latency_ms: 3 },
            { node_id: 'residential_002', allocated_power: 30, source_mix: { solar: 30 }, action: 'reduce', latency_ms: 4 },
          ];
          break;
        case 2: // Severe shortage
          newAllocations = [
            { node_id: 'hospital_001_icu', allocated_power: 60, source_mix: { battery: 60 }, action: 'maintain', latency_ms: 5 },
            { node_id: 'hospital_001_ventilators', allocated_power: 30, source_mix: { battery: 30 }, action: 'maintain', latency_ms: 4 },
            { node_id: 'hospital_001_hallways', allocated_power: 0, source_mix: {}, action: 'cutoff', latency_ms: 3 },
            { node_id: 'hospital_001_canteen', allocated_power: 0, source_mix: {}, action: 'cutoff', latency_ms: 3 },
            { node_id: 'factory_001', allocated_power: 200, source_mix: { solar: 200 }, action: 'reduce', latency_ms: 7 },
            { node_id: 'factory_002', allocated_power: 150, source_mix: { grid: 150 }, action: 'reduce', latency_ms: 8 },
            { node_id: 'residential_001', allocated_power: 0, source_mix: {}, action: 'cutoff', latency_ms: 3 },
            { node_id: 'residential_002', allocated_power: 0, source_mix: {}, action: 'cutoff', latency_ms: 4 },
          ];
          break;
        default:
          newAllocations = [...sampleAllocations];
      }
      
      // Apply slight variations to give a "live" feel
      newAllocations = newAllocations.map(alloc => ({
        ...alloc,
        allocated_power: alloc.allocated_power > 0 ? Math.max(0, alloc.allocated_power + (Math.random() * 10 - 5)) : 0,
        latency_ms: Math.max(1, alloc.latency_ms + (Math.random() * 2 - 1))
      }));
      
      setDemoAllocations(newAllocations);
      setDemoTime(time);
    };

    updateAllocations();
    const interval = setInterval(updateAllocations, 500);
    return () => clearInterval(interval);
  }, [showDemo, wsState.isConnected, wsData.allocations.length]);

  // Use real data if available, otherwise use sample data
  const allocationsToUse = wsData.allocations.length > 0 ? wsData.allocations : (showDemo ? demoAllocations : sampleAllocations);
  
  const nodes = allocationsToUse.length > 0 
    ? allocationsToUse.map(allocation => {
        // Find corresponding sample node or create a basic one
        const sampleNode = sampleNodes.find(n => n.node_id === allocation.node_id);
        return sampleNode || {
          node_id: allocation.node_id,
          current_load: (sampleNodes.find(n => n.node_id === allocation.node_id)?.current_load || allocation.allocated_power) + (Math.random() * 4 - 2),
          priority_tier: allocation.node_id.includes('hospital') ? 1 : 
                        allocation.node_id.includes('factory') ? 2 : 3,
          source_type: Object.keys(allocation.source_mix)[0] as any || 'Grid',
          status: allocation.action === 'cutoff' ? 'inactive' : 'active',
          location: { lat: 28.6139 + Math.random() * 0.01, lng: 77.2090 + Math.random() * 0.01 },
          timestamp: allocation.timestamp || Date.now(),
        } as EnergyNode;
      })
    : sampleNodes;
  
  const allocations = allocationsToUse;

  // Calculate total supply and demand for gauges
  const totalDemand = nodes.reduce((sum, node) => sum + node.current_load, 0);
  const totalSupply = allocations.reduce((sum, allocation) => sum + allocation.allocated_power, 0);
  const maxCapacity = 1200; // Maximum grid capacity in kW

  const getScenarioDescription = () => {
    const cycle = Math.floor(demoTime / 3000) % 3;
    switch (cycle) {
      case 0: return "Normal Operation - All nodes receiving full power";
      case 1: return "Moderate Shortage - Factories and residential areas reduced";
      case 2: return "Severe Shortage - Residential areas cut off, hospitals maintained";
      default: return "Initializing...";
    }
  };

  // Render Dashboard Content
  const renderDashboard = () => (
    <div className="space-y-8">
      {/* WebSocket Connection Demo */}
      <WebSocketDemo />
      
      {/* Predictive Action Alert Banner */}
      {wsData.predictiveMessage && (
        <div className={`p-4 rounded-lg border flex items-center justify-between shadow-lg animate-[pulse_2s_ease-in-out_infinite] ${
          wsData.predictiveMessage.action === 'storm_warning' 
            ? 'bg-blue-900/40 border-blue-500' 
            : 'bg-purple-900/40 border-purple-500'
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              wsData.predictiveMessage.action === 'storm_warning' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
            }`}>
              <svg className="w-6 h-6 animate-[bounce_2s_infinite]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {wsData.predictiveMessage.action === 'storm_warning' ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                )}
              </svg>
            </div>
            <div>
              <h3 className={`font-semibold ${
                wsData.predictiveMessage.action === 'storm_warning' ? 'text-blue-400' : 'text-purple-400'
              }`}>
                {wsData.predictiveMessage.action === 'storm_warning' ? 'Storm Warning Active' : 'Peak Load Forecast Active'}
              </h3>
              <p className="text-white text-sm mt-1">{wsData.predictiveMessage.message}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Demo Toggle */}
      <div className="flex justify-center">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center space-x-4">
            <span className="text-white font-medium">View Mode:</span>
            <button
              onClick={() => setShowDemo(true)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showDemo 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Live Demo
            </button>
            <button
              onClick={() => setShowDemo(false)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                !showDemo 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Static View
            </button>
          </div>
        </div>
      </div>

      {/* Power Connection Map Area */}
      {showDemo && wsData.allocations.length === 0 && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Live Simulation Demo</h3>
              <p className="text-slate-300 text-sm">{getScenarioDescription()}</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Cycle Updates Every 3s</div>
              <div className="text-xs text-slate-500">Last Update: {new Date(demoTime).toLocaleTimeString()}</div>
            </div>
          </div>
        </div>
      )}
      <div className={`lg:col-span-2 ${isGridDown ? 'opacity-90 saturate-50' : ''}`}>
        <PowerMap nodes={nodes} allocations={allocations} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Real-time Gauges */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">System Metrics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className={isGridDown ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.8)]' : ''}>
              <LiveGauge
                title="Total Supply"
                value={totalSupply}
                max={maxCapacity}
                unit="kW"
                color="blue"
              />
            </div>
            <div className={isGridDown ? 'opacity-30 grayscale' : ''}>
              <LiveGauge
                title="Total Demand"
                value={totalDemand}
                max={maxCapacity}
                unit="kW"
                color={totalDemand > totalSupply ? "red" : totalDemand > totalSupply * 0.8 ? "yellow" : "green"}
              />
            </div>
          </div>
        </div>

        {/* Real-Time Energy Graph */}
        <div className={`${isGridDown ? 'ring-2 ring-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)] rounded-lg' : ''}`}>
          <EnergyGraph 
            totalSupply={totalSupply}
            totalDemand={totalDemand}
            decisionLatency={wsData.latency}
          />
        </div>

        {/* Live Stream Table */}
        <div className={`card ${isGridDown ? 'opacity-30 grayscale' : ''}`}>
          <StreamTable 
            allocations={allocations}
            maxRows={12}
          />
        </div>

        {/* Simulation Control Panel */}
        <div className="card lg:col-span-2">
          <SimulationPanel 
            onSimulate={handleSimulate}
            isSimulating={isSimulating}
          />
        </div>
      </div>
    </div>
  );

  return (
    <Layout 
      activeTab={activeTab} 
      onTabChange={setActiveTab}
      isGridDown={isGridDown}
      onGridToggle={handleGridToggle}
      wsState={wsState}
    >
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'priority' && <PriorityController />}
    </Layout>
  )
}

export default App