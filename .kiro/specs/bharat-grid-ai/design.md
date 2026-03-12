# Technical Design: Bharat-Grid AI

## Overview
Bharat-Grid AI is a real-time energy distribution optimization system designed for the "Hack for Green Bharat" hackathon. The system reduces carbon footprint by intelligently managing power distribution across critical infrastructure, minimizing diesel generator usage, and ensuring hospitals and factories remain operational during grid failures.

## High-Level Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │   React Dashboard (Tailwind CSS)                   │    │
│  │   - Power Connection Map                           │    │
│  │   - Real-time Gauges                               │    │
│  │   - Live Stream Table                              │    │
│  │   - Grid Failure Simulator                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                    WebSocket / REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │   FastAPI Server                                   │    │
│  │   - WebSocket endpoints                            │    │
│  │   - REST endpoints                                 │    │
│  │   - Latency tracking                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Stream Processing Layer                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │   Pathway Framework                                │    │
│  │   - Real-time data ingestion                       │    │
│  │   - Priority algorithm (O(n))                      │    │
│  │   - Power allocation engine                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      AI Layer                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │   RAG System (Pathway + LLM)                       │    │
│  │   - Vector store (consumption patterns)           │    │
│  │   - Demand prediction                              │    │
│  │   - Optimization insights                          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│   JSON/CSV Streams  │  Historical Data  │  Grid Sensors     │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Data Ingestion Module
- **Purpose**: Ingest real-time energy data from multiple sources
- **Technology**: Pathway streaming connectors
- **Input Formats**: JSON, CSV streams
- **Output**: Normalized data stream to processing engine

#### 2. Priority Allocation Engine
- **Purpose**: Execute O(n) priority algorithm for power distribution
- **Target Latency**: <10ms
- **Algorithm**: Single-pass priority-based allocation
- **Triggers**: Supply drop events, grid failures

#### 3. RAG Prediction System
- **Purpose**: Predict energy demand and generate insights
- **Components**:
  - Vector database (Pinecone or ChromaDB)
  - Pathway LLM connector
  - Historical pattern analyzer
- **Output**: Demand forecasts, optimization recommendations

#### 4. API Gateway
- **Purpose**: Bridge between Pathway and frontend
- **Technology**: FastAPI
- **Features**: WebSocket streaming, REST endpoints, latency metrics

#### 5. Dashboard UI
- **Purpose**: Real-time visualization and control
- **Technology**: React 18, Tailwind CSS, WebSocket client
- **Features**: Live gauges, connection map, simulation controls

### Data Models

#### Node Schema
```typescript
interface EnergyNode {
  node_id: string;
  current_load: number;        // in kW
  priority_tier: 1 | 2 | 3;    // 1=Hospital, 2=Factory, 3=Residential
  source_type: 'Grid' | 'Solar' | 'Battery' | 'Diesel';
  status: 'active' | 'inactive' | 'degraded';
  location: {
    lat: number;
    lng: number;
  };
  timestamp: number;
}
```

#### Supply Event Schema
```typescript
interface SupplyEvent {
  event_id: string;
  total_supply: number;         // in kW
  available_sources: {
    grid: number;
    solar: number;
    battery: number;
    diesel: number;
  };
  timestamp: number;
}
```

#### Allocation Result Schema
```typescript
interface AllocationResult {
  node_id: string;
  allocated_power: number;
  source_mix: {
    grid?: number;
    solar?: number;
    battery?: number;
    diesel?: number;
  };
  action: 'maintain' | 'reduce' | 'cutoff';
  latency_ms: number;
}
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Stream Processing | Pathway | Real-time data processing |
| API | FastAPI | REST/WebSocket server |
| Frontend | React 18 + Tailwind | Dashboard UI |
| AI/ML | Pathway LLM + Vector DB | RAG predictions |
| Data Storage | ChromaDB/Pinecone | Vector embeddings |
| WebSocket | FastAPI WebSocket | Real-time updates |

## Low-Level Design

### Priority Allocation Algorithm

**Objective**: Allocate available power to nodes based on priority tiers in O(n) time with <10ms latency.

**Algorithm Pseudocode**:
```python
def allocate_power(nodes: List[Node], total_supply: float) -> List[Allocation]:
    # Sort nodes by priority (O(n log n) preprocessing, done once)
    sorted_nodes = sort_by_priority(nodes)  # Tier 1 first, then 2, then 3
    
    allocations = []
    remaining_supply = total_supply
    
    # Single pass allocation (O(n))
    for node in sorted_nodes:
        if remaining_supply >= node.current_load:
            # Full allocation
            allocations.append({
                'node_id': node.node_id,
                'allocated': node.current_load,
                'action': 'maintain'
            })
            remaining_supply -= node.current_load
        elif remaining_supply > 0:
            # Partial allocation
            allocations.append({
                'node_id': node.node_id,
                'allocated': remaining_supply,
                'action': 'reduce'
            })
            remaining_supply = 0
        else:
            # No allocation
            allocations.append({
                'node_id': node.node_id,
                'allocated': 0,
                'action': 'cutoff'
            })
    
    return allocations
```

**Optimization**: Use priority queue for dynamic updates.

### Pathway Stream Processing Pipeline

**File**: `backend/pathway_engine.py`

```python
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex

class EnergyOptimizer:
    def __init__(self):
        self.nodes_table = None
        self.supply_table = None
        
    def create_pipeline(self):
        # Input connectors
        self.nodes_table = pw.io.csv.read(
            './data/nodes_stream.csv',
            schema=NodeSchema,
            mode='streaming'
        )
        
        self.supply_table = pw.io.jsonlines.read(
            './data/supply_stream.jsonl',
            schema=SupplySchema,
            mode='streaming'
        )
        
        # Join nodes with latest supply
        combined = self.nodes_table.join(
            self.supply_table,
            self.nodes_table.timestamp == self.supply_table.timestamp
        )
        
        # Apply priority allocation
        allocations = combined.select(
            node_id=pw.this.node_id,
            allocated_power=pw.apply(
                self.allocate_power,
                pw.this.current_load,
                pw.this.priority_tier,
                pw.this.total_supply
            )
        )
        
        # Output to API
        pw.io.jsonlines.write(allocations, './output/allocations.jsonl')
        
        return allocations
```

### RAG System Implementation

**File**: `backend/rag_system.py`

```python
import pathway as pw
from pathway.xpacks.llm import embedders, llms

class EnergyRAG:
    def __init__(self, vector_store_path: str):
        self.embedder = embedders.OpenAIEmbedder()
        self.llm = llms.OpenAIChat()
        self.index = None
        
    def build_index(self, historical_data: pw.Table):
        # Embed consumption patterns
        embedded = historical_data.select(
            text=pw.this.pattern_description,
            embedding=self.embedder(pw.this.pattern_description)
        )
        
        # Create KNN index
        self.index = KNNIndex(embedded, d=1536)
        
    def predict_demand(self, current_context: str) -> str:
        # Retrieve similar patterns
        query_embedding = self.embedder(current_context)
        similar_patterns = self.index.query(query_embedding, k=5)
        
        # Generate prediction using LLM
        prompt = f"""
        Based on these historical patterns:
        {similar_patterns}
        
        Current context: {current_context}
        
        Predict energy demand for the next hour and suggest optimization strategies.
        """
        
        prediction = self.llm(prompt)
        return prediction
```

### FastAPI Integration

**File**: `backend/api.py`

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket for real-time updates
@app.websocket("/ws/allocations")
async def websocket_allocations(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        # Read from Pathway output
        allocation_data = read_latest_allocations()
        
        # Track latency
        start_time = time.perf_counter()
        await websocket.send_json(allocation_data)
        latency = (time.perf_counter() - start_time) * 1000
        
        # Send latency metric
        await websocket.send_json({
            'type': 'latency',
            'value': latency
        })
        
        await asyncio.sleep(0.1)  # 100ms update rate

@app.post("/simulate/grid-failure")
async def simulate_grid_failure(failure_percentage: float):
    # Inject supply drop event into Pathway stream
    inject_supply_event({
        'total_supply': current_supply * (1 - failure_percentage),
        'timestamp': time.time()
    })
    
    return {'status': 'simulated', 'reduction': failure_percentage}

@app.get("/insights")
async def get_insights():
    # Query RAG system
    insights = rag_system.predict_demand(get_current_context())
    return {'insights': insights}
```

### React Dashboard Components

**File**: `frontend/src/components/PowerMap.tsx`

```typescript
interface PowerMapProps {
  nodes: EnergyNode[];
  allocations: AllocationResult[];
}

export const PowerMap: React.FC<PowerMapProps> = ({ nodes, allocations }) => {
  return (
    <div className="relative w-full h-96 bg-slate-900 rounded-lg">
      {/* Central Hub */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <div className="w-16 h-16 bg-blue-500 rounded-full animate-pulse" />
      </div>
      
      {/* Nodes */}
      {nodes.map((node, idx) => (
        <NodeConnection
          key={node.node_id}
          node={node}
          allocation={allocations.find(a => a.node_id === node.node_id)}
          position={calculatePosition(idx, nodes.length)}
        />
      ))}
    </div>
  );
};
```

**File**: `frontend/src/hooks/useWebSocket.ts`

```typescript
export const useWebSocket = (url: string) => {
  const [data, setData] = useState<any>(null);
  const [latency, setLatency] = useState<number>(0);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'latency') {
        setLatency(message.value);
      } else {
        setData(message);
      }
    };
    
    return () => ws.close();
  }, [url]);
  
  return { data, latency };
};
```

### Directory Structure

```
bharat-grid-ai/
├── backend/
│   ├── pathway_engine.py       # Stream processing core
│   ├── rag_system.py           # AI prediction system
│   ├── api.py                  # FastAPI server
│   ├── schemas.py              # Data models
│   └── utils/
│       ├── priority_algo.py    # O(n) allocation algorithm
│       └── latency_tracker.py  # Performance monitoring
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PowerMap.tsx
│   │   │   ├── LiveGauge.tsx
│   │   │   ├── StreamTable.tsx
│   │   │   └── SimulationPanel.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tailwind.config.js
├── data/
│   ├── nodes_stream.csv        # Simulated node data
│   ├── supply_stream.jsonl     # Simulated supply events
│   └── historical/             # Training data for RAG
├── requirements.txt
├── README.md
└── docker-compose.yml
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Allocation Latency | <10ms | Time from supply event to allocation decision |
| WebSocket Latency | <50ms | Time from allocation to frontend update |
| RAG Response Time | <2s | Time to generate insights |
| Dashboard FPS | 60fps | Smooth animations and updates |

### Scalability Considerations

1. **Horizontal Scaling**: Pathway supports distributed processing across multiple nodes
2. **Vector Store**: Use managed Pinecone for production, ChromaDB for development
3. **Caching**: Redis layer for frequently accessed predictions
4. **Load Balancing**: Nginx for API gateway
5. **Monitoring**: Prometheus + Grafana for metrics

## Security & Compliance

- API authentication via JWT tokens
- Rate limiting on simulation endpoints
- Input validation for all data streams
- Audit logging for all allocation decisions
- HTTPS/WSS for all communications

## Testing Strategy

- Unit tests for priority algorithm
- Integration tests for Pathway pipeline
- Load tests for <10ms latency validation
- E2E tests for dashboard functionality
- Chaos engineering for grid failure scenarios
