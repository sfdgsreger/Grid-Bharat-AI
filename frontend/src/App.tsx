import { useState } from 'react'
import Layout from './components/Layout'
import WebSocketDemo from './components/WebSocketDemo'
import PowerMap from './components/PowerMap'
import PowerMapDemo from './components/PowerMapDemo'
import LiveGauge from './components/LiveGauge'
import StreamTable from './components/StreamTable'
import SimulationPanel from './components/SimulationPanel'
import PriorityController from './components/PriorityController'
import { useWebSocket } from './hooks/useWebSocket'
import type { EnergyNode, AllocationResult } from './types'

function App() {
  // WebSocket connection for real-time data
  const { data: wsData } = useWebSocket();
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
    // Reset simulation state after a delay to allow for backend processing
    setTimeout(() => {
      setIsSimulating(false);
    }, 2000);
  };

  // Sample data for demonstration when no real data is available
  const sampleNodes: EnergyNode[] = [
    {
      node_id: 'hospital_001',
      current_load: 150,
      priority_tier: 1,
      source_type: 'Grid',
      status: 'active',
      location: { lat: 28.6139, lng: 77.2090 },
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
      node_id: 'hospital_002',
      current_load: 200,
      priority_tier: 1,
      source_type: 'Diesel',
      status: 'active',
      location: { lat: 28.6180, lng: 77.2120 },
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
      node_id: 'hospital_001',
      allocated_power: 150,
      source_mix: { grid: 150 },
      action: 'maintain',
      latency_ms: 5,
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
      node_id: 'hospital_002',
      allocated_power: 200,
      source_mix: { diesel: 200 },
      action: 'maintain',
      latency_ms: 6,
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

  // Use real data if available, otherwise use sample data
  const nodes = wsData.allocations.length > 0 
    ? wsData.allocations.map(allocation => {
        // Find corresponding sample node or create a basic one
        const sampleNode = sampleNodes.find(n => n.node_id === allocation.node_id);
        return sampleNode || {
          node_id: allocation.node_id,
          current_load: allocation.allocated_power,
          priority_tier: allocation.node_id.includes('hospital') ? 1 : 
                        allocation.node_id.includes('factory') ? 2 : 3,
          source_type: Object.keys(allocation.source_mix)[0] as any || 'Grid',
          status: allocation.action === 'cutoff' ? 'inactive' : 'active',
          location: { lat: 28.6139 + Math.random() * 0.01, lng: 77.2090 + Math.random() * 0.01 },
          timestamp: allocation.timestamp || Date.now(),
        } as EnergyNode;
      })
    : sampleNodes;
  
  const allocations = wsData.allocations.length > 0 ? wsData.allocations : sampleAllocations;

  // Calculate total supply and demand for gauges
  const totalDemand = nodes.reduce((sum, node) => sum + node.current_load, 0);
  const totalSupply = allocations.reduce((sum, allocation) => sum + allocation.allocated_power, 0);
  const maxCapacity = 1200; // Maximum grid capacity in kW

  // Render Dashboard Content
  const renderDashboard = () => (
    <div className="space-y-8">
      {/* WebSocket Connection Demo */}
      <WebSocketDemo />
      
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

      {/* Power Connection Map */}
      {showDemo ? (
        <PowerMapDemo />
      ) : (
        <div className={`lg:col-span-2 ${isGridDown ? 'opacity-90 saturate-50' : ''}`}>
          <PowerMap nodes={nodes} allocations={allocations} />
        </div>
      )}
      
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
    >
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'priority' && <PriorityController />}
    </Layout>
  )
}

export default App