#!/usr/bin/env python3
"""
Development Stream Manager for Bharat-Grid AI
Easy-to-use interface for managing development data streams
"""

import os
import sys
import json
import time
import argparse
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stream_config import DataStreamManager
from failure_scenarios import generate_failure_scenarios
from data_generators import generate_complete_dataset

class DevStreamManager:
    """High-level interface for development data streams"""
    
    def __init__(self, config_path: str = "backend/data/stream_config.json"):
        self.stream_manager = DataStreamManager(config_path)
        self.running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down streams...")
        self.stop()
        sys.exit(0)
    
    def start(self, background: bool = False):
        """Start development data streams"""
        if self.running:
            print("Streams are already running")
            return
        
        print("Starting Bharat-Grid AI development data streams...")
        self.stream_manager.start_streams()
        self.running = True
        
        if not background:
            self._run_interactive()
    
    def stop(self):
        """Stop development data streams"""
        if not self.running:
            print("Streams are not running")
            return
        
        print("Stopping development data streams...")
        self.stream_manager.stop_streams()
        self.running = False
        print("Streams stopped successfully")
    
    def status(self) -> Dict[str, Any]:
        """Get current status of all streams"""
        return self.stream_manager.get_stream_status()
    
    def trigger_failure(self, scenario: str, duration: Optional[int] = None) -> bool:
        """Trigger a grid failure scenario"""
        return self.stream_manager.trigger_failure_scenario(scenario, duration)
    
    def list_scenarios(self) -> List[str]:
        """List available failure scenarios"""
        return list(self.stream_manager.failure_scenarios.keys())
    
    def _run_interactive(self):
        """Run interactive monitoring loop"""
        print("\nDevelopment streams are running...")
        print("Commands:")
        print("  status  - Show stream status")
        print("  fail    - Trigger failure scenario")
        print("  list    - List failure scenarios")
        print("  stop    - Stop streams")
        print("  help    - Show this help")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while self.running:
                try:
                    command = input("dev-streams> ").strip().lower()
                    
                    if command == "status":
                        self._show_status()
                    elif command == "fail":
                        self._interactive_failure()
                    elif command == "list":
                        self._list_scenarios()
                    elif command == "stop":
                        self.stop()
                        break
                    elif command == "help":
                        self._show_help()
                    elif command == "":
                        continue
                    else:
                        print(f"Unknown command: {command}. Type 'help' for available commands.")
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def _show_status(self):
        """Show detailed stream status"""
        status = self.status()
        print(f"\nStream Status:")
        print(f"  Running: {status['running']}")
        print(f"  Active Streams: {status['active_streams']}")
        
        for stream_name, stream_info in status['streams'].items():
            print(f"\n  {stream_name}:")
            print(f"    Active: {stream_info['active']}")
            if 'file_info' in stream_info:
                size_mb = stream_info['file_info']['size_mb']
                print(f"    File Size: {size_mb:.2f} MB")
            
            if 'state' in stream_info and 'active_failures' in stream_info['state']:
                failures = stream_info['state']['active_failures']
                if failures:
                    print(f"    Active Failures: {len(failures)}")
                    for failure in failures:
                        print(f"      - {failure.get('scenario', 'unknown')}")
    
    def _interactive_failure(self):
        """Interactive failure scenario trigger"""
        scenarios = self.list_scenarios()
        
        print("\nAvailable failure scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"  {i}. {scenario}")
        
        try:
            choice = input("\nSelect scenario (number or name): ").strip()
            
            # Try to parse as number
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(scenarios):
                    scenario = scenarios[idx]
                else:
                    print("Invalid scenario number")
                    return
            except ValueError:
                # Try as scenario name
                if choice in scenarios:
                    scenario = choice
                else:
                    print("Invalid scenario name")
                    return
            
            duration_input = input("Duration in minutes (press Enter for random): ").strip()
            duration = None
            if duration_input:
                try:
                    duration = int(duration_input)
                except ValueError:
                    print("Invalid duration, using random")
            
            if self.trigger_failure(scenario, duration):
                print(f"Triggered failure scenario: {scenario}")
                if duration:
                    print(f"Duration: {duration} minutes")
            else:
                print("Failed to trigger scenario")
                
        except KeyboardInterrupt:
            print("\nCancelled")
    
    def _list_scenarios(self):
        """List all available failure scenarios"""
        scenarios = self.list_scenarios()
        print(f"\nAvailable failure scenarios ({len(scenarios)}):")
        for scenario in scenarios:
            scenario_info = self.stream_manager.failure_scenarios[scenario]
            print(f"  {scenario}: {scenario_info.description}")
    
    def _show_help(self):
        """Show help information"""
        print("\nAvailable commands:")
        print("  status  - Show current status of all streams")
        print("  fail    - Interactively trigger a failure scenario")
        print("  list    - List all available failure scenarios")
        print("  stop    - Stop all streams and exit")
        print("  help    - Show this help message")
        print("\nStream files are located in backend/data/streams/")
        print("Configuration is stored in backend/data/stream_config.json")

def main():
    """Main entry point for development stream manager"""
    parser = argparse.ArgumentParser(description="Bharat-Grid AI Development Stream Manager")
    parser.add_argument("--config", default="backend/data/stream_config.json",
                       help="Path to stream configuration file")
    parser.add_argument("--background", action="store_true",
                       help="Run in background mode (no interactive shell)")
    parser.add_argument("--generate-data", action="store_true",
                       help="Generate initial sample data before starting streams")
    
    args = parser.parse_args()
    
    # Generate initial data if requested
    if args.generate_data:
        print("Generating initial sample data...")
        generate_complete_dataset()
        generate_failure_scenarios()
        print("Sample data generation complete")
    
    # Start stream manager
    manager = DevStreamManager(args.config)
    
    try:
        manager.start(background=args.background)
        
        if args.background:
            # Keep running in background
            while manager.running:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        manager.stop()

if __name__ == "__main__":
    main()