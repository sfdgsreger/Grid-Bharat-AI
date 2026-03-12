# 🚀 Bharat-Grid AI - Quick Reference Guide

## 🎯 What Does This Project Do?

**Bharat-Grid AI** is a real-time energy distribution system that:
1. **Prioritizes critical infrastructure** during power shortages (hospitals > factories > residential)
2. **Minimizes carbon footprint** by preferring clean energy (solar > battery > grid > diesel)
3. **Responds in real-time** with <10ms allocation decisions
4. **Predicts demand** using AI/RAG system
5. **Visualizes everything** in a beautiful real-time dashboard

---

## 🛠️ Tech Stack Summary

### Backend (Python)
- **FastAPI**: Web server with WebSocket support
- **Pathway**: Real-time stream processing framework
- **ChromaDB**: Vector database for AI embeddings
- **OpenAI API**: LLM for demand predictions
- **Uvicorn**: ASGI server

### Frontend (TypeScript/React)
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool
- **dnd-kit**: Drag-and-drop library
- **Framer Motion**: Animation library

### AI/ML
- **RAG System**: Retrieval-Augmented Generation
- **Vector Embeddings**: 1536-dimensional (OpenAI)
- **Similarity Search**: KNN index
- **LLM**: GPT-4 / GPT-3.5-turbo

---

## 🔄 How It Works (Simple Explanation)

### 1. Data Collection
```
Grid Sensors → CSV/JSON Streams → Pathway Engine
```
- Collects real-time data from power grid
- Monitors hospitals, factories, residential areas
- Tracks available power from solar, grid, battery, diesel

### 2. Smart Allocation
```
Pathway Engine → Priority Algorithm → Allocation Results
```
- Sorts facilities by priority (hospitals first)
- Allocates available power intelligently
- Decides: maintain, reduce, or cutoff power
- Completes in <10ms

### 3. AI Predictions
```
Historical Data → Vector Store → RAG System → Insights
```
- Stores past consumption patterns
- Finds similar historical situations
- Uses AI to predict future demand
- Suggests optimizations

### 4. Real-Time Updates
```
Allocation Results → WebSocket → React Dashboard
```
- Broadcasts updates every 3 seconds
- Updates dashboard in real-time
- Shows visual effects for grid failures
- Maintains 60fps animations

---

## 🎮 Key Features Explained

### Feature 1: Grid Failure Simulation

**What it does:**
- Simulates power grid failures
- Shows how system prioritizes critical loads
- Visual feedback with colors and effects

**How it works:**
1. User clicks red "SIMULATE GRID FAILURE" button
2. Backend reduces available power supply
3. Algorithm reallocates power (hospitals first)
4. Frontend shows:
   - Hospitals glow green (getting power)
   - Residential areas fade (power cut)
   - Button turns green "RESTORE GRID"

**Technology:**
- React state management
- Tailwind CSS conditional classes
- WebSocket real-time updates

### Feature 2: Priority Controller

**What it does:**
- Drag-and-drop interface to set priorities
- Configure which facilities get power first
- Save configurations for different scenarios

**How it works:**
1. User drags facility cards between tiers
2. Frontend tracks tier assignments
3. Save button sends configuration to backend
4. Backend uses priorities for allocation decisions

**Technology:**
- dnd-kit for drag-and-drop
- Framer Motion for animations
- React state for tier management

### Feature 3: Real-Time Dashboard

**What it does:**
- Shows live power distribution
- Displays supply vs demand
- Updates every 3 seconds
- Smooth 60fps animations

**How it works:**
1. Backend generates allocation data
2. WebSocket broadcasts to frontend
3. React hooks receive updates
4. Components re-render with new data
5. Framer Motion animates transitions

**Technology:**
- WebSocket for real-time data
- React hooks (useState, useEffect)
- Tailwind CSS for styling
- Lucide React for icons

### Feature 4: AI Insights (RAG System)

**What it does:**
- Predicts energy demand
- Suggests optimizations
- Based on historical patterns

**How it works:**
1. **Store Historical Data:**
   ```
   Consumption Pattern → OpenAI Embedder → 1536-dim Vector → ChromaDB
   ```

2. **Query for Predictions:**
   ```
   User Query → Embed Query → Find Similar Patterns (KNN) → Top 5 Matches
   ```

3. **Generate Insights:**
   ```
   Similar Patterns + Current Context → GPT-4 → Prediction + Recommendations
   ```

**Technology:**
- Pathway LLM integration
- ChromaDB vector store
- OpenAI embeddings & GPT-4
- KNN similarity search

---

## 🔧 How Technologies Interact

### Complete Request Flow

```
┌─────────────┐
│   Browser   │ User clicks "Simulate Grid Failure"
└──────┬──────┘
       │ HTTP POST
       ↓
┌─────────────┐
│   FastAPI   │ Receives request, reduces supply
└──────┬──────┘
       │ Triggers
       ↓
┌─────────────┐
│   Pathway   │ Processes supply event, runs allocation algorithm
└──────┬──────┘
       │ Generates
       ↓
┌─────────────┐
│ Allocations │ Results: Hospital=150kW, Factory=0kW, Residential=0kW
└──────┬──────┘
       │ Broadcasts via
       ↓
┌─────────────┐
│  WebSocket  │ Sends JSON to all connected clients
└──────┬──────┘
       │ Receives
       ↓
┌─────────────┐
│ React Hook  │ useWebSocket updates state
└──────┬──────┘
       │ Triggers
       ↓
┌─────────────┐
│  Dashboard  │ Re-renders with new data, shows visual effects
└─────────────┘
```

### RAG System Flow

```
┌──────────────┐
│ User Request │ "Predict hospital demand"
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ OpenAI Embed │ Query → 1536-dimensional vector
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  ChromaDB    │ KNN search for similar patterns
└──────┬───────┘
       │ Returns top 5
       ↓
┌──────────────┐
│ GPT-4 / 3.5  │ Generates prediction based on patterns
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   Insights   │ "Expected: 185kW, Recommendation: Pre-allocate backup"
└──────────────┘
```

---

## 📊 Data Models

### Energy Node
```typescript
{
  node_id: "hospital_001",
  current_load: 150,           // kW
  priority_tier: 1,            // 1=Critical, 2=Essential, 3=Non-Essential
  source_type: "Grid",         // Grid | Solar | Battery | Diesel
  status: "active",            // active | inactive | degraded
  location: { lat: 28.6139, lng: 77.2090 },
  timestamp: 1703123456789
}
```

### Allocation Result
```typescript
{
  node_id: "hospital_001",
  allocated_power: 150,        // kW allocated
  source_mix: {                // Where power comes from
    solar: 100,
    grid: 50
  },
  action: "maintain",          // maintain | reduce | cutoff
  latency_ms: 5,               // Processing time
  timestamp: 1703123456789
}
```

---

## 🚀 Quick Commands

### Development
```bash
# Backend
cd backend && venv\Scripts\activate && python debug_backend.py

# Frontend
cd frontend && npm run dev
```

### Production
```bash
docker-compose up -d
```

### Testing
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

---

## 🎯 Performance Targets

- ⚡ **Allocation**: <10ms per decision
- 🔌 **WebSocket**: <50ms transmission
- 🤖 **RAG System**: <2s response
- 🎨 **Dashboard**: 60fps rendering

---

## 💡 Use Cases

1. **Grid Failure Response**: Automatically prioritize hospitals during outages
2. **Carbon Reduction**: Prefer solar/battery over diesel generators
3. **Demand Forecasting**: Predict peak loads and prepare resources
4. **Priority Management**: Configure which facilities get power first
5. **Real-Time Monitoring**: Track energy distribution across the grid

---

**Built for Hack for Green Bharat 🇮🇳**