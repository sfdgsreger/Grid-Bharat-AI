#!/usr/bin/env python3
"""
Utility functions for working with development data streams
"""

import json
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

def read_latest_stream_data(stream_file: str, num_records: int = 10) -> List[Dict]:
    """Read the latest records from a stream file"""
    
    file_path = Path(stream_file)
    if not file_path.exists():
        return []
    
    records = []
    
    if file_path.suffix == '.csv':
        # Read CSV file
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            records = list(reader)
    
    elif file_path.suffix == '.jsonl':
        # Read JSONL file
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError:
                    continue
    
    # Return latest records
    return records[-num_records:] if records else []

def monitor_stream_files(duration_seconds: int = 60, interval_seconds: int = 5):
    """Monitor stream files for changes"""
    
    stream_files = [
        "backend/data/streams/nodes_stream.csv",
        "backend/data/streams/nodes_stream.jsonl", 
        "backend/data/streams/supply_events.jsonl",
        "backend/data/streams/failure_scenarios.jsonl"
    ]
    
    print(f"Monitoring stream files for {duration_seconds} seconds...")
    print("File sizes will be checked every {interval_seconds} seconds")
    print("-" * 60)
    
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] Stream file sizes:")
        
        for file_path in stream_files:
            path = Path(file_path)
            if path.exists():
                size_kb = path.stat().st_size / 1024
                print(f"  {path.name}: {size_kb:.1f} KB")
            else:
                print(f"  {path.name}: Not found")
        
        time.sleep(interval_seconds)
    
    print(f"\nMonitoring completed after {duration_seconds} seconds")

def analyze_stream_data(stream_file: str) -> Dict[str, Any]:
    """Analyze stream data and provide statistics"""
    
    records = read_latest_stream_data(stream_file, num_records=1000)  # Analyze last 1000 records
    
    if not records:
        return {"error": "No data found"}
    
    analysis = {
        "total_records": len(records),
        "file_path": stream_file,
        "analysis_time": datetime.now().isoformat()
    }
    
    # Analyze based on file type
    file_path = Path(stream_file)
    
    if "nodes" in file_path.name:
        analysis.update(_analyze_node_data(records))
    elif "supply" in file_path.name:
        analysis.update(_analyze_supply_data(records))
    elif "failure" in file_path.name:
        analysis.update(_analyze_failure_data(records))
    
    return analysis

def _analyze_node_data(records: List[Dict]) -> Dict[str, Any]:
    """Analyze energy node data"""
    
    if not records:
        return {}
    
    # Extract numeric values
    loads = []
    priority_counts = {1: 0, 2: 0, 3: 0}
    status_counts = {}
    source_counts = {}
    
    for record in records:
        # Load analysis
        try:
            load = float(record.get('current_load', 0))
            loads.append(load)
        except (ValueError, TypeError):
            pass
        
        # Priority analysis
        priority = record.get('priority_tier')
        if priority in priority_counts:
            priority_counts[priority] += 1
        
        # Status analysis
        status = record.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Source analysis
        source = record.get('source_type', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    analysis = {
        "node_analysis": {
            "load_statistics": {
                "min_load": min(loads) if loads else 0,
                "max_load": max(loads) if loads else 0,
                "avg_load": sum(loads) / len(loads) if loads else 0,
                "total_load": sum(loads) if loads else 0
            },
            "priority_distribution": priority_counts,
            "status_distribution": status_counts,
            "source_distribution": source_counts
        }
    }
    
    return analysis

def _analyze_supply_data(records: List[Dict]) -> Dict[str, Any]:
    """Analyze supply event data"""
    
    if not records:
        return {}
    
    total_supplies = []
    source_totals = {"grid": [], "solar": [], "battery": [], "diesel": []}
    
    for record in records:
        # Total supply
        try:
            total = float(record.get('total_supply', 0))
            total_supplies.append(total)
        except (ValueError, TypeError):
            pass
        
        # Source breakdown
        sources = record.get('available_sources', {})
        for source_type in source_totals:
            try:
                value = float(sources.get(source_type, 0))
                source_totals[source_type].append(value)
            except (ValueError, TypeError):
                pass
    
    analysis = {
        "supply_analysis": {
            "total_supply_statistics": {
                "min_supply": min(total_supplies) if total_supplies else 0,
                "max_supply": max(total_supplies) if total_supplies else 0,
                "avg_supply": sum(total_supplies) / len(total_supplies) if total_supplies else 0
            },
            "source_statistics": {}
        }
    }
    
    # Calculate statistics for each source
    for source_type, values in source_totals.items():
        if values:
            analysis["supply_analysis"]["source_statistics"][source_type] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "total": sum(values)
            }
    
    return analysis

def _analyze_failure_data(records: List[Dict]) -> Dict[str, Any]:
    """Analyze failure scenario data"""
    
    if not records:
        return {}
    
    scenario_counts = {}
    severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    durations = []
    
    for record in records:
        # Scenario type
        scenario_type = record.get('scenario_type', 'unknown')
        scenario_counts[scenario_type] = scenario_counts.get(scenario_type, 0) + 1
        
        # Severity level
        severity = record.get('severity_level')
        if severity in severity_counts:
            severity_counts[severity] += 1
        
        # Duration
        try:
            duration = float(record.get('duration_minutes', 0))
            durations.append(duration)
        except (ValueError, TypeError):
            pass
    
    analysis = {
        "failure_analysis": {
            "scenario_distribution": scenario_counts,
            "severity_distribution": severity_counts,
            "duration_statistics": {
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "avg_duration": sum(durations) / len(durations) if durations else 0
            }
        }
    }
    
    return analysis

def export_stream_sample(stream_file: str, output_file: str, num_records: int = 100):
    """Export a sample of stream data to a new file"""
    
    records = read_latest_stream_data(stream_file, num_records)
    
    if not records:
        print(f"No data found in {stream_file}")
        return
    
    output_path = Path(output_file)
    
    if output_path.suffix == '.json':
        # Export as JSON
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2)
    
    elif output_path.suffix == '.csv':
        # Export as CSV
        if records:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
    
    else:
        # Export as JSONL
        with open(output_path, 'w') as f:
            for record in records:
                json.dump(record, f)
                f.write('\n')
    
    print(f"Exported {len(records)} records to {output_file}")

def clean_old_stream_files(max_age_hours: int = 24):
    """Clean up old rotated stream files"""
    
    streams_dir = Path("backend/data/streams")
    if not streams_dir.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_files = []
    
    for file_path in streams_dir.glob("*_*"):  # Files with timestamp pattern
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    cleaned_files.append(file_path.name)
                except OSError as e:
                    print(f"Failed to delete {file_path.name}: {e}")
    
    if cleaned_files:
        print(f"Cleaned up {len(cleaned_files)} old stream files:")
        for filename in cleaned_files:
            print(f"  - {filename}")
    else:
        print("No old stream files found to clean up")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stream utilities for Bharat-Grid AI")
    parser.add_argument("command", choices=["monitor", "analyze", "export", "clean"],
                       help="Command to execute")
    parser.add_argument("--file", help="Stream file path")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--records", type=int, default=100, help="Number of records")
    parser.add_argument("--age", type=int, default=24, help="Max age in hours")
    
    args = parser.parse_args()
    
    if args.command == "monitor":
        monitor_stream_files(args.duration)
    
    elif args.command == "analyze":
        if not args.file:
            print("Error: --file required for analyze command")
            exit(1)
        
        analysis = analyze_stream_data(args.file)
        print(json.dumps(analysis, indent=2))
    
    elif args.command == "export":
        if not args.file or not args.output:
            print("Error: --file and --output required for export command")
            exit(1)
        
        export_stream_sample(args.file, args.output, args.records)
    
    elif args.command == "clean":
        clean_old_stream_files(args.age)