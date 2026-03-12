// Core TypeScript interfaces for Bharat-Grid AI frontend

export interface Location {
  lat: number;
  lng: number;
}

export interface EnergyNode {
  node_id: string;
  current_load: number; // in kW
  priority_tier: 1 | 2 | 3; // 1=Hospital, 2=Factory, 3=Residential
  source_type: 'Grid' | 'Solar' | 'Battery' | 'Diesel';
  status: 'active' | 'inactive' | 'degraded';
  location: Location;
  timestamp: number;
}

export interface AvailableSources {
  grid: number;
  solar: number;
  battery: number;
  diesel: number;
}

export interface SupplyEvent {
  event_id: string;
  total_supply: number; // in kW
  available_sources: AvailableSources;
  timestamp: number;
}

export interface SourceMix {
  grid?: number;
  solar?: number;
  battery?: number;
  diesel?: number;
}

export interface AllocationResult {
  node_id: string;
  allocated_power: number;
  source_mix: SourceMix;
  action: 'maintain' | 'reduce' | 'cutoff';
  latency_ms: number;
  timestamp?: number; // Optional timestamp for frontend display
}

// Additional types for frontend components
export interface GridFailureRequest {
  failure_percentage: number; // 0.0-1.0
}

export interface GridFailureResponse {
  status: string;
  reduction: number;
}

export interface InsightsResponse {
  insights: string;
  timestamp: number;
}

export interface LatencyMetric {
  type: 'latency';
  value: number; // in milliseconds
}

// WebSocket message types
export type WebSocketMessage = AllocationResult | LatencyMetric;

// Component prop types
export interface PowerMapProps {
  nodes: EnergyNode[];
  allocations: AllocationResult[];
}

export interface LiveGaugeProps {
  title: string;
  value: number;
  max: number;
  unit: string;
  color?: 'blue' | 'green' | 'yellow' | 'red';
}

export interface StreamTableProps {
  allocations: AllocationResult[];
  maxRows?: number;
}

export interface SimulationPanelProps {
  onSimulate: (percentage: number) => void;
  isSimulating: boolean;
}