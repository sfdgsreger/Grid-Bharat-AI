# Sample Data Generators for Bharat-Grid AI

This document explains how to use the sample data generators to create realistic test data for the Bharat-Grid AI system.

## Overview

The data generators create three types of sample data:

1. **Energy Node Data Streams** - Real-time energy consumption data from hospitals, factories, and residential areas
2. **Supply Event Simulation Data** - Power supply events with varying scenarios (normal, peak demand, grid failures, renewable peaks)
3. **Historical Consumption Patterns** - Training data for the RAG system to learn from past consumption behaviors

## Quick Start

### Generate Complete Dataset

```bash
# Generate full 24-hour dataset with 30 days of history
python backend/generate_sample_data.py

# Generate quick test dataset (2 hours, 7 days history)
python backend/generate_sample_data.py --quick

# Generate and populate RAG system
python backend/generate_sample_data.py --populate-rag
```

### Custom Generation

```bash
# Custom parameters
python backend/generate_sample_data.py \
  --duration-hours 48 \
  --history-days 60 \
  --nodes-per-type 10 \
  --output-dir ./custom_data \
  --populate-rag
```

## Generated Data Structure

```
backend/data/generated/
├── nodes_stream.csv           # Energy node data (CSV format)
├── nodes_stream.jsonl         # Energy node data (JSON Lines)
├── supply_events.jsonl        # Supply events data
├── historical_patterns.csv    # Historical consumption patterns
├── dataset_stats.json         # Generation statistics
└── vector_store/             # RAG system vector database (if --populate-rag used)
```

## Data Formats

### Energy Node Data

**CSV Format** (`nodes_stream.csv`):
```csv
node_id,current_load,priority_tier,source_type,status,lat,lng,timestamp
hospital_001,156.78,1,Grid,active,28.6139,77.2090,1703123456.789
factory_001,287.45,2,Solar,active,28.4595,77.0266,1703123456.789
residential_001,89.23,3,Grid,active,28.5355,77.3910,1703123456.789
```

**JSON Lines Format** (`nodes_stream.jsonl`):
```json
{"node_id": "hospital_001", "current_load": 156.78, "priority_tier": 1, "source_type": "Grid", "status": "active", "location": {"lat": 28.6139, "lng": 77.2090}, "timestamp": 1703123456.789}
```

### Supply Events Data

**JSON Lines Format** (`supply_events.jsonl`):
```json
{"event_id": "supply_1703123456_0001", "total_supply": 2456.78, "available_sources": {"grid": 1474.07, "solar": 614.20, "battery": 245.68, "diesel": 122.84}, "timestamp": 1703123456.789}
```

### Historical Patterns Data

**CSV Format** (`historical_patterns.csv`):
```csv
pattern_id,timestamp,node_id,context,current_load,peak_load,avg_load,duration_hours,node_type,pattern_type,priority_tier,weather_condition
hospital_001_pattern_0001,1703023456.789,hospital_001,"Normal operational pattern for hospital during morning hours",145.67,189.37,138.64,6.45,hospital,normal_operation,1,clear
```

## Node Types and Characteristics

### Hospital Nodes (Priority Tier 1)
- **Base Load**: 120-200 kW
- **Peak Hours**: 7-9 AM, 6-10 PM
- **Source Preference**: Grid → Battery → Diesel
- **Locations**: Major Indian cities (Delhi, Mumbai, Chennai, Kolkata, Bangalore)

### Factory Nodes (Priority Tier 2)
- **Base Load**: 200-400 kW
- **Peak Hours**: 8 AM - 6 PM (business hours)
- **Source Preference**: Grid → Solar → Battery
- **Locations**: Industrial areas (Gurgaon, Andheri, Guindy, Salt Lake, Electronic City)

### Residential Nodes (Priority Tier 3)
- **Base Load**: 50-120 kW
- **Peak Hours**: 6-8 AM, 7-11 PM
- **Source Preference**: Grid → Solar
- **Locations**: Residential areas (Noida, Bandra, T Nagar, Park Street, Whitefield)

## Supply Scenarios

### Normal Operations
- **Total Supply**: 2000-3000 kW
- **Source Mix**: 60% Grid, 25% Solar, 10% Battery, 5% Diesel
- **Variability**: Low (10%)

### Peak Demand
- **Total Supply**: 1800-2500 kW
- **Source Mix**: 50% Grid, 20% Solar, 20% Battery, 10% Diesel
- **Variability**: Medium (20%)

### Grid Failure
- **Total Supply**: 800-1200 kW
- **Source Mix**: 0% Grid, 40% Solar, 35% Battery, 25% Diesel
- **Variability**: High (30%)

### Renewable Peak
- **Total Supply**: 2500-3500 kW
- **Source Mix**: 30% Grid, 60% Solar, 8% Battery, 2% Diesel
- **Variability**: Medium (15%)

## Historical Pattern Types

### Normal Operation (60% frequency)
- **Load Multiplier**: 0.8-1.2x base load
- **Duration**: 4-12 hours
- **Description**: Standard operational patterns

### Emergency Surge (10% frequency)
- **Load Multiplier**: 1.5-2.5x base load
- **Duration**: 1-6 hours
- **Description**: Emergency or high-demand situations

### Maintenance Mode (15% frequency)
- **Load Multiplier**: 0.1-0.4x base load
- **Duration**: 2-8 hours
- **Description**: Reduced load during maintenance

### Peak Efficiency (15% frequency)
- **Load Multiplier**: 1.1-1.4x base load
- **Duration**: 6-16 hours
- **Description**: Optimized high-efficiency operation

## Using Generated Data

### With Pathway Engine

```python
import pathway as pw
from schemas import EnergyNode, SupplyEvent

# Read generated node data
nodes_table = pw.io.csv.read(
    './backend/data/generated/nodes_stream.csv',
    schema=EnergyNode,
    mode='streaming'
)

# Read generated supply events
supply_table = pw.io.jsonlines.read(
    './backend/data/generated/supply_events.jsonl',
    schema=SupplyEvent,
    mode='streaming'
)
```

### With RAG System

```python
from rag_system import EnergyRAG, load_historical_data_from_csv

# Initialize RAG system
rag = EnergyRAG(vector_store_path="./backend/data/generated/vector_store")

# Load historical patterns
patterns = load_historical_data_from_csv('./backend/data/generated/historical_patterns.csv')
rag.add_patterns_batch(patterns)

# Test prediction
from rag_system import PredictionRequest
request = PredictionRequest(
    current_context="Hospital experiencing increased patient load during evening hours",
    node_ids=["hospital_001"],
    time_horizon=2
)
response = rag.generate_prediction(request)
```

### With API Testing

```python
import requests
import json

# Load sample data for API testing
with open('./backend/data/generated/supply_events.jsonl', 'r') as f:
    sample_event = json.loads(f.readline())

# Test grid failure simulation
response = requests.post('http://localhost:8000/simulate/grid-failure', 
                        json={'failure_percentage': 0.3})
```

## Customization

### Adding New Node Types

```python
from data_generators import EnergyNodeGenerator

# Extend node types
gen = EnergyNodeGenerator()
gen.node_types['datacenter'] = {
    'priority_tier': 2,
    'base_load': (500, 800),
    'load_variance': 0.2,
    'peak_hours': [(0, 24)],  # 24/7 operation
    'source_preference': ['Grid', 'Battery'],
    'locations': [(28.6139, 77.2090)]  # Delhi
}
```

### Custom Supply Scenarios

```python
from data_generators import SupplyEventGenerator

gen = SupplyEventGenerator()
gen.scenarios['custom_scenario'] = {
    'total_supply_range': (1500, 2000),
    'source_distribution': {
        'grid': 0.4, 'solar': 0.3, 'battery': 0.2, 'diesel': 0.1
    },
    'variability': 0.25
}
```

### Custom Pattern Templates

```python
from data_generators import HistoricalPatternGenerator

gen = HistoricalPatternGenerator()
gen.pattern_templates['custom_pattern'] = {
    'description': "Custom operational pattern",
    'load_multiplier': (1.0, 1.5),
    'duration_hours': (3, 8),
    'frequency': 0.2
}
```

## Performance Considerations

- **Node Data**: 1-minute intervals generate ~1,440 points per node per day
- **Supply Events**: 5-minute intervals generate ~288 events per day
- **Historical Patterns**: ~10-20 patterns per node per day of history
- **Memory Usage**: ~1MB per 1000 data points
- **Generation Time**: ~10-30 seconds for full dataset

## Integration with Existing System

The generated data is fully compatible with:

- ✅ **Pathway Engine** - Direct CSV/JSONL ingestion
- ✅ **RAG System** - Historical pattern loading
- ✅ **FastAPI Server** - JSON format compatibility
- ✅ **React Dashboard** - WebSocket data streaming
- ✅ **Testing Framework** - Realistic test scenarios

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the backend directory
2. **Permission Errors**: Check write permissions for output directory
3. **Memory Issues**: Reduce `duration_hours` or `nodes_per_type` for large datasets
4. **RAG Population Fails**: Ensure OpenAI API key is set or use mock embeddings

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run generation with debug output
from data_generators import generate_complete_dataset
stats = generate_complete_dataset(duration_hours=1)  # Small test
```

## Examples

See the following files for usage examples:
- `backend/test_with_sample_data.py` - API testing with generated data
- `backend/demo_rag_system.py` - RAG system with historical patterns
- `backend/performance_demo.py` - Performance testing with realistic loads