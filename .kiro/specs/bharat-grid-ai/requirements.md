# Requirements Document

## Introduction

Bharat-Grid AI is a real-time energy distribution optimization system that reduces carbon footprint by intelligently managing power distribution across critical infrastructure. The system minimizes diesel generator usage and ensures hospitals and factories remain operational during grid failures through priority-based allocation and AI-driven demand prediction.

## Glossary

- **System**: The complete Bharat-Grid AI platform including all components
- **Priority_Allocator**: The O(n) algorithm component that distributes power based on priority tiers
- **RAG_System**: The Retrieval-Augmented Generation system for demand prediction
- **Dashboard**: The React-based frontend visualization interface
- **API_Gateway**: The FastAPI server providing REST and WebSocket endpoints
- **Stream_Processor**: The Pathway framework component handling real-time data ingestion
- **Energy_Node**: A power consumption point (hospital, factory, or residential)
- **Supply_Event**: A change in available power supply from various sources
- **Allocation_Result**: The output specifying power distribution to each node
- **Vector_Store**: The database storing historical consumption pattern embeddings
- **WebSocket_Client**: The frontend component receiving real-time updates

## Requirements

### Requirement 1: Real-Time Data Ingestion

**User Story:** As a grid operator, I want the system to ingest real-time energy data from multiple sources, so that allocation decisions are based on current conditions.

#### Acceptance Criteria

1. WHEN a JSON stream is provided, THE Stream_Processor SHALL parse it into normalized Energy_Node records
2. WHEN a CSV stream is provided, THE Stream_Processor SHALL parse it into normalized Energy_Node records
3. WHEN a Supply_Event arrives, THE Stream_Processor SHALL process it within 10ms
4. THE Stream_Processor SHALL validate all incoming data against the defined schemas
5. WHEN invalid data is received, THE Stream_Processor SHALL log the error and continue processing valid records

### Requirement 2: Priority-Based Power Allocation

**User Story:** As a grid operator, I want power allocated based on priority tiers, so that critical infrastructure remains operational during supply shortages.

#### Acceptance Criteria

1. WHEN total supply exceeds total demand, THE Priority_Allocator SHALL allocate full requested power to all Energy_Nodes
2. WHEN total supply is less than total demand, THE Priority_Allocator SHALL allocate power to tier 1 nodes before tier 2 nodes
3. WHEN total supply is less than total demand, THE Priority_Allocator SHALL allocate power to tier 2 nodes before tier 3 nodes
4. WHEN an Energy_Node cannot receive full power, THE Priority_Allocator SHALL allocate partial power if supply remains
5. WHEN no supply remains for an Energy_Node, THE Priority_Allocator SHALL set allocated power to zero
6. THE Priority_Allocator SHALL complete allocation decisions within 10ms for any number of nodes
7. THE Priority_Allocator SHALL produce an Allocation_Result for every Energy_Node in the input

### Requirement 3: AI-Driven Demand Prediction

**User Story:** As a grid operator, I want AI-powered demand forecasts, so that I can proactively manage power distribution.

#### Acceptance Criteria

1. WHEN historical consumption data is provided, THE RAG_System SHALL build a vector index of consumption patterns
2. WHEN a demand prediction is requested, THE RAG_System SHALL retrieve the 5 most similar historical patterns
3. WHEN similar patterns are retrieved, THE RAG_System SHALL generate a demand forecast using the LLM
4. THE RAG_System SHALL return predictions within 2 seconds
5. WHEN generating predictions, THE RAG_System SHALL include optimization recommendations in the response

### Requirement 4: Real-Time Dashboard Updates

**User Story:** As a grid operator, I want real-time visualization of power distribution, so that I can monitor system status continuously.

#### Acceptance Criteria

1. WHEN an Allocation_Result is generated, THE API_Gateway SHALL broadcast it to all connected WebSocket_Clients within 50ms
2. WHEN a WebSocket_Client connects, THE Dashboard SHALL display the power connection map
3. WHEN an Allocation_Result is received, THE Dashboard SHALL update node visualizations within one frame
4. THE Dashboard SHALL maintain 60 frames per second during updates
5. WHEN latency data is received, THE Dashboard SHALL display the current latency metric

### Requirement 5: Grid Failure Simulation

**User Story:** As a system tester, I want to simulate grid failures, so that I can validate the system's response to supply disruptions.

#### Acceptance Criteria

1. WHEN a grid failure simulation is triggered, THE API_Gateway SHALL inject a Supply_Event with reduced total supply
2. WHEN a failure percentage is specified, THE API_Gateway SHALL reduce total supply by that percentage
3. WHEN a simulation is triggered, THE System SHALL return a confirmation with the reduction percentage
4. WHEN a Supply_Event is injected, THE Priority_Allocator SHALL process it using the standard allocation algorithm

### Requirement 6: Data Model Compliance

**User Story:** As a developer, I want consistent data structures across all components, so that integration is reliable and maintainable.

#### Acceptance Criteria

1. THE System SHALL define Energy_Node with fields: node_id, current_load, priority_tier, source_type, status, location, timestamp
2. THE System SHALL define Supply_Event with fields: event_id, total_supply, available_sources, timestamp
3. THE System SHALL define Allocation_Result with fields: node_id, allocated_power, source_mix, action, latency_ms
4. WHEN an Energy_Node is created, THE System SHALL validate that priority_tier is 1, 2, or 3
5. WHEN an Energy_Node is created, THE System SHALL validate that source_type is Grid, Solar, Battery, or Diesel
6. WHEN an Allocation_Result is created, THE System SHALL validate that action is maintain, reduce, or cutoff

### Requirement 7: Performance Monitoring

**User Story:** As a system administrator, I want latency metrics tracked and reported, so that I can ensure performance targets are met.

#### Acceptance Criteria

1. WHEN an allocation decision is made, THE Priority_Allocator SHALL record the processing time in milliseconds
2. WHEN an Allocation_Result is sent via WebSocket, THE API_Gateway SHALL record the transmission time
3. THE API_Gateway SHALL include latency_ms in every Allocation_Result
4. WHEN latency exceeds 10ms for allocation, THE System SHALL log a performance warning
5. WHEN WebSocket latency exceeds 50ms, THE System SHALL log a performance warning

### Requirement 8: API Endpoints

**User Story:** As a frontend developer, I want well-defined API endpoints, so that I can integrate the dashboard with the backend.

#### Acceptance Criteria

1. THE API_Gateway SHALL provide a WebSocket endpoint at /ws/allocations for real-time updates
2. THE API_Gateway SHALL provide a POST endpoint at /simulate/grid-failure for triggering simulations
3. THE API_Gateway SHALL provide a GET endpoint at /insights for retrieving AI predictions
4. WHEN /simulate/grid-failure is called, THE API_Gateway SHALL accept a failure_percentage parameter
5. WHEN /insights is called, THE API_Gateway SHALL return predictions from the RAG_System
6. THE API_Gateway SHALL enable CORS for all origins during development

### Requirement 9: Source Mix Optimization

**User Story:** As a sustainability officer, I want power allocated from clean sources first, so that carbon footprint is minimized.

#### Acceptance Criteria

1. WHEN allocating power, THE Priority_Allocator SHALL prefer solar over grid power
2. WHEN allocating power, THE Priority_Allocator SHALL prefer battery over diesel power
3. WHEN allocating power, THE Priority_Allocator SHALL use diesel only when other sources are exhausted
4. WHEN an Allocation_Result is generated, THE System SHALL include the source_mix breakdown
5. THE System SHALL track total diesel usage across all allocations

### Requirement 10: Error Handling and Resilience

**User Story:** As a grid operator, I want the system to handle errors gracefully, so that temporary issues don't cause system-wide failures.

#### Acceptance Criteria

1. WHEN a data parsing error occurs, THE Stream_Processor SHALL log the error and continue processing
2. WHEN the RAG_System fails to generate a prediction, THE API_Gateway SHALL return a fallback response
3. WHEN a WebSocket connection drops, THE Dashboard SHALL attempt to reconnect automatically
4. WHEN the vector store is unavailable, THE RAG_System SHALL return an error message without crashing
5. WHEN invalid input is provided to any endpoint, THE API_Gateway SHALL return a descriptive error message

### Requirement 11: Historical Data Management

**User Story:** As a data analyst, I want historical consumption patterns stored and indexed, so that the RAG system can learn from past behavior.

#### Acceptance Criteria

1. WHEN historical data is loaded, THE RAG_System SHALL embed each consumption pattern using the configured embedder
2. WHEN embeddings are generated, THE RAG_System SHALL store them in the Vector_Store
3. THE RAG_System SHALL create a KNN index with dimensionality 1536 for OpenAI embeddings
4. WHEN querying for similar patterns, THE RAG_System SHALL use the KNN index for retrieval
5. THE Vector_Store SHALL persist embeddings across system restarts

### Requirement 12: Dashboard Visualization Components

**User Story:** As a grid operator, I want intuitive visual components, so that I can quickly understand system status at a glance.

#### Acceptance Criteria

1. THE Dashboard SHALL display a power connection map showing all Energy_Nodes
2. THE Dashboard SHALL display real-time gauges for total supply and total demand
3. THE Dashboard SHALL display a live stream table of recent Allocation_Results
4. THE Dashboard SHALL display a simulation control panel for triggering grid failures
5. WHEN an Energy_Node status changes, THE Dashboard SHALL update the node's visual representation
6. WHEN an allocation action is cutoff, THE Dashboard SHALL display the node in red
7. WHEN an allocation action is reduce, THE Dashboard SHALL display the node in yellow
8. WHEN an allocation action is maintain, THE Dashboard SHALL display the node in green
