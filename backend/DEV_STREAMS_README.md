# Development Data Streams - Bharat-Grid AI

## Overview

The development data streams provide continuous, realistic energy data for testing and development of the Bharat-Grid AI system. The streams simulate real-world energy distribution scenarios with automatic data rotation, variation, and failure scenario injection.

## Features

### 🔄 **Continuous Data Streams**
- **CSV Streams**: Compatible with Pathway CSV connectors
- **JSON Lines Streams**: Compatible with Pathway JSONL connectors
- **Automatic Rotation**: Files rotate based on size and time intervals
- **Data Variation**: Realistic load variations and status changes
- **Failure Injection**: Automatic grid failure scenario simulation

### 📊 **Stream Types**

#### 1. Energy Node Streams
- **Format**: CSV and JSONL
- **Update Interval**: 15-30 seconds
- **Content**: Real-time energy node data with load, priority, status, and location
- **Files**: 
  - `backend/data/streams/nodes_stream.csv`
  - `backend/data/streams/nodes_stream.jsonl`

#### 2. Supply Event Streams
- **Format**: JSONL
- **Update Interval**: 60 seconds
- **Content**: Power supply availability from different sources (grid, solar, battery, diesel)
- **File**: `backend/data/streams/supply_events.jsonl`

#### 3. Failure Scenario Streams
- **Format**: JSONL
- **Update Interval**: 300 seconds (5 minutes)
- **Content**: Grid failure events with severity levels and recovery patterns
- **File**: `backend/data/streams/failure_scenarios.jsonl`

### ⚡ **Failure Scenarios**

The system includes 6 types of realistic failure scenarios:

1. **Grid Blackout** - Complete grid power failure
2. **Solar Cloud Cover** - Reduced solar output due to weather
3. **Battery Degradation** - Battery system performance issues
4. **Diesel Shortage** - Fuel shortage for backup generators
5. **Cascade Failure** - Multi-source failures
6. **Cyber Attack** - System disruption from security breaches

Each scenario has:
- **Severity Levels**: 1-5 scale
- **Duration**: Realistic time ranges
- **Recovery Patterns**: Immediate, gradual, or stepped recovery
- **Source Impact**: Specific effects on different power sources

## Quick Start

### 1. Setup Development Streams

```bash
# Initialize streams with sample data
python backend/setup_dev_streams.py

# Validate setup
python backend/setup_dev_streams.py --validate-only
```

### 2. Start Streaming

```bash
# Interactive mode (with command shell)
python backend/dev_stream_manager.py

# Background mode
python backend/dev_stream_manager.py --background

# With fresh data generation
python backend/dev_stream_manager.py --generate-data
```

### 3. Test Functionality

```bash
# Run comprehensive test
python backend/test_dev_streams.py
```

## Interactive Commands

When running in interactive mode, use these commands:

- `status` - Show current stream status and file sizes
- `fail` - Trigger a failure scenario interactively
- `list` - List all available failure scenarios
- `stop` - Stop all streams and exit
- `help` - Show command help

## Configuration

### Stream Configuration (`backend/data/stream_config.json`)

```json
{
  "streams": {
    "nodes_csv": {
      "output_format": "csv",
      "update_interval_seconds": 30,
      "rotation_interval_minutes": 60,
      "variation_factor": 0.3,
      "enable_failures": true,
      "failure_probability": 0.02,
      "max_file_size_mb": 10,
      "keep_history_files": 24
    }
  }
}
```

### Key Parameters

- **update_interval_seconds**: How often new data is generated
- **rotation_interval_minutes**: How often files are rotated
- **variation_factor**: Amount of random variation (0.0-1.0)
- **enable_failures**: Whether to inject failure scenarios
- **failure_probability**: Chance of failure per update cycle
- **max_file_size_mb**: Maximum file size before rotation
- **keep_history_files**: Number of rotated files to keep

## Data Schema

### Energy Node Data

```json
{
  "node_id": "hospital_001",
  "current_load": 245.67,
  "priority_tier": 1,
  "source_type": "Grid",
  "status": "active",
  "location": {
    "lat": 28.6139,
    "lng": 77.2090
  },
  "timestamp": 1773246688.218
}
```

### Supply Event Data

```json
{
  "event_id": "supply_1773246688_0001",
  "total_supply": 2245.63,
  "available_sources": {
    "grid": 802.81,
    "solar": 642.19,
    "battery": 800.63,
    "diesel": 0.0
  },
  "timestamp": 1773246688.218
}
```

### Failure Scenario Data

```json
{
  "event_id": "failure_0001_grid_blackout",
  "scenario_type": "grid_blackout",
  "severity_level": 3,
  "duration_minutes": 120.5,
  "affected_sources": ["grid"],
  "recovery_pattern": "gradual",
  "impact_description": "Complete Grid Blackout (Severity 3)",
  "pre_failure_supply": {
    "grid": 1500.0,
    "solar": 400.0,
    "battery": 300.0,
    "diesel": 200.0,
    "total": 2400.0
  },
  "during_failure_supply": {
    "grid": 150.0,
    "solar": 400.0,
    "battery": 300.0,
    "diesel": 200.0,
    "total": 1050.0
  }
}
```

## Integration with Pathway

### CSV Stream Connection

```python
import pathway as pw

# Connect to CSV stream
nodes_table = pw.io.csv.read(
    './backend/data/streams/nodes_stream.csv',
    schema=NodeSchema,
    mode='streaming'
)
```

### JSONL Stream Connection

```python
# Connect to JSONL stream
supply_table = pw.io.jsonlines.read(
    './backend/data/streams/supply_events.jsonl',
    schema=SupplySchema,
    mode='streaming'
)
```

## File Structure

```
backend/data/
├── streams/                    # Active stream files
│   ├── nodes_stream.csv       # CSV node data
│   ├── nodes_stream.jsonl     # JSONL node data
│   ├── supply_events.jsonl    # Supply events
│   └── failure_scenarios.jsonl # Failure scenarios
├── generated/                  # Initial sample data
├── failure_scenarios/          # Failure scenario datasets
├── historical/                 # Historical patterns for RAG
└── stream_config.json         # Stream configuration
```

## Performance Characteristics

- **Data Generation**: ~1000 records/second
- **File Rotation**: Automatic based on size/time
- **Memory Usage**: <50MB for stream manager
- **CPU Usage**: <5% during normal operation
- **Disk Usage**: ~100MB/day with default settings

## Monitoring and Logging

The stream manager provides detailed logging:

```
INFO:stream_config:Starting data streams...
INFO:stream_config:Stream nodes_csv started
WARNING:stream_config:Triggered failure scenario 'grid_outage' for 120.5 minutes
INFO:stream_config:Rotated stream file: nodes_csv -> nodes_stream_20250109_143022.csv
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write access to `backend/data/streams/`
2. **Port Conflicts**: Check if other processes are using stream files
3. **Memory Issues**: Reduce `nodes_per_type` in configuration
4. **Disk Space**: Monitor disk usage and adjust `keep_history_files`

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=backend
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from dev_stream_manager import DevStreamManager
manager = DevStreamManager()
manager.start()
"
```

## API Integration

The streams integrate seamlessly with the FastAPI server:

```python
# In your FastAPI application
from stream_config import DataStreamManager

# Initialize stream manager
stream_manager = DataStreamManager()
stream_manager.start_streams()

# Trigger failures via API
@app.post("/simulate/grid-failure")
async def simulate_failure(failure_percentage: float):
    # This will be reflected in the streams
    stream_manager.trigger_failure_scenario("grid_blackout", duration=60)
```

## Development Tips

1. **Start Small**: Begin with short durations and few nodes
2. **Monitor Files**: Watch file sizes to understand data generation rates
3. **Test Failures**: Use interactive mode to test failure scenarios
4. **Validate Data**: Check generated data structure before integration
5. **Performance**: Monitor system resources during long runs

## Next Steps

1. **Integration**: Connect streams to Pathway engine
2. **Monitoring**: Add Prometheus metrics for production
3. **Scaling**: Implement distributed streaming for larger datasets
4. **Validation**: Add data quality checks and alerts
5. **Visualization**: Create real-time stream monitoring dashboard

---

**Note**: This development stream system is designed for testing and development. For production use, consider implementing proper data validation, error recovery, and monitoring systems.