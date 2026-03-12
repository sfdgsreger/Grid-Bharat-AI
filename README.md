# Bharat-Grid AI

A real-time energy distribution optimization system that reduces carbon footprint by intelligently managing power distribution across critical infrastructure. Built for the "Hack for Green Bharat" hackathon.

## Overview

Bharat-Grid AI minimizes diesel generator usage and ensures hospitals and factories remain operational during grid failures through priority-based allocation and AI-driven demand prediction.

## Architecture

- **Backend**: Python (FastAPI + Pathway) for real-time stream processing
- **Frontend**: TypeScript (React + Tailwind CSS) for dashboard visualization
- **AI**: RAG system with vector database for demand prediction
- **Performance**: <10ms allocation latency, <50ms WebSocket updates

## Key Features

- **Priority-Based Allocation**: Hospitals (Tier 1) > Factories (Tier 2) > Residential (Tier 3)
- **Source Mix Optimization**: Solar > Grid > Battery > Diesel for carbon reduction
- **Real-Time Dashboard**: Live power connection map with 60fps updates
- **AI Predictions**: Demand forecasting with optimization recommendations
- **Grid Failure Simulation**: Test system resilience under supply disruptions

## Data Models

### Energy Node
- `node_id`: Unique identifier
- `current_load`: Power demand in kW
- `priority_tier`: 1=Hospital, 2=Factory, 3=Residential
- `source_type`: Grid/Solar/Battery/Diesel
- `status`: active/inactive/degraded
- `location`: Geographic coordinates
- `timestamp`: Unix timestamp

### Supply Event
- `event_id`: Unique identifier
- `total_supply`: Available power in kW
- `available_sources`: Power breakdown by source
- `timestamp`: Unix timestamp

### Allocation Result
- `node_id`: Target node identifier
- `allocated_power`: Assigned power in kW
- `source_mix`: Power breakdown by source
- `action`: maintain/reduce/cutoff
- `latency_ms`: Processing time

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Additional setup will be implemented in subsequent tasks
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Performance Targets

- **Allocation Latency**: <10ms
- **WebSocket Latency**: <50ms  
- **RAG Response Time**: <2s
- **Dashboard FPS**: 60fps

## Development Status

This project is currently in development. Task 1 (project structure and data models) has been completed. Subsequent tasks will implement the core allocation algorithm, stream processing, AI predictions, and dashboard components.

## License

MIT License - Built for Hack for Green Bharat hackathon