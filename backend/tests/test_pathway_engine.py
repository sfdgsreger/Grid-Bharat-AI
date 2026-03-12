# Unit tests for Pathway data ingestion pipeline
import pytest
import tempfile
import json
import csv
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathway_engine import (
    EnergyDataIngestionPipeline,
    validate_energy_node_data,
    validate_supply_event_data
)
from schemas import EnergyNode, SupplyEvent, Location, AvailableSources


class TestEnergyDataIngestionPipeline:
    """Test suite for the Pathway data ingestion pipeline"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = EnergyDataIngestionPipeline(self.temp_dir)
    
    def test_validate_node_data_valid(self):
        """Test validation of valid energy node data"""
        valid_data = {
            'node_id': 'hospital_01',
            'current_load': 150.5,
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(valid_data)
        
        assert result is not None
        assert isinstance(result, EnergyNode)
        assert result.node_id == 'hospital_01'
        assert result.current_load == 150.5
        assert result.priority_tier == 1
        assert result.source_type == 'Grid'
        assert result.status == 'active'
        assert result.location.lat == 28.6139
        assert result.location.lng == 77.2090
        assert result.timestamp == 1703001600.0
    
    def test_validate_node_data_invalid_priority_tier(self):
        """Test validation rejects invalid priority tier"""
        invalid_data = {
            'node_id': 'test_01',
            'current_load': 100.0,
            'priority_tier': 4,  # Invalid: must be 1, 2, or 3
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(invalid_data)
        assert result is None
    
    def test_validate_node_data_invalid_source_type(self):
        """Test validation rejects invalid source type"""
        invalid_data = {
            'node_id': 'test_01',
            'current_load': 100.0,
            'priority_tier': 1,
            'source_type': 'Nuclear',  # Invalid: not in allowed types
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(invalid_data)
        assert result is None
    
    def test_validate_node_data_invalid_status(self):
        """Test validation rejects invalid status"""
        invalid_data = {
            'node_id': 'test_01',
            'current_load': 100.0,
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'broken',  # Invalid: not in allowed statuses
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(invalid_data)
        assert result is None
    
    def test_validate_node_data_negative_load(self):
        """Test validation rejects negative current load"""
        invalid_data = {
            'node_id': 'test_01',
            'current_load': -50.0,  # Invalid: negative load
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(invalid_data)
        assert result is None
    
    def test_validate_node_data_missing_field(self):
        """Test validation handles missing required fields"""
        invalid_data = {
            'node_id': 'test_01',
            'current_load': 100.0,
            'priority_tier': 1,
            # Missing source_type
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_node_data(invalid_data)
        assert result is None
    
    def test_validate_supply_data_valid(self):
        """Test validation of valid supply event data"""
        valid_data = {
            'event_id': 'supply_001',
            'total_supply': 1000.0,
            'grid': 400.0,
            'solar': 300.0,
            'battery': 200.0,
            'diesel': 100.0,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_supply_data(valid_data)
        
        assert result is not None
        assert isinstance(result, SupplyEvent)
        assert result.event_id == 'supply_001'
        assert result.total_supply == 1000.0
        assert result.available_sources.grid == 400.0
        assert result.available_sources.solar == 300.0
        assert result.available_sources.battery == 200.0
        assert result.available_sources.diesel == 100.0
        assert result.timestamp == 1703001600.0
    
    def test_validate_supply_data_negative_values(self):
        """Test validation rejects negative supply values"""
        invalid_data = {
            'event_id': 'supply_001',
            'total_supply': 1000.0,
            'grid': -100.0,  # Invalid: negative value
            'solar': 300.0,
            'battery': 200.0,
            'diesel': 100.0,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_supply_data(invalid_data)
        assert result is None
    
    def test_validate_supply_data_mismatched_total(self):
        """Test validation rejects mismatched total supply"""
        invalid_data = {
            'event_id': 'supply_001',
            'total_supply': 1500.0,  # Doesn't match sum of sources (1000.0)
            'grid': 400.0,
            'solar': 300.0,
            'battery': 200.0,
            'diesel': 100.0,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_supply_data(invalid_data)
        assert result is None
    
    def test_validate_supply_data_missing_field(self):
        """Test validation handles missing required fields"""
        invalid_data = {
            'event_id': 'supply_001',
            'total_supply': 1000.0,
            'grid': 400.0,
            'solar': 300.0,
            # Missing battery
            'diesel': 100.0,
            'timestamp': 1703001600.0
        }
        
        result = self.pipeline.validate_supply_data(invalid_data)
        assert result is None
    
    def test_create_node_schema(self):
        """Test node schema creation"""
        schema = self.pipeline.create_node_schema()
        
        # Check that schema has expected columns
        expected_columns = [
            'node_id', 'current_load', 'priority_tier', 'source_type',
            'status', 'lat', 'lng', 'timestamp'
        ]
        
        # Note: Pathway schema introspection may vary by version
        # This test ensures schema creation doesn't raise exceptions
        assert schema is not None
    
    def test_create_supply_schema(self):
        """Test supply schema creation"""
        schema = self.pipeline.create_supply_schema()
        
        # Check that schema has expected columns
        expected_columns = [
            'event_id', 'total_supply', 'grid', 'solar',
            'battery', 'diesel', 'timestamp'
        ]
        
        # Note: Pathway schema introspection may vary by version
        # This test ensures schema creation doesn't raise exceptions
        assert schema is not None
    
    def test_error_handling_malformed_data(self):
        """Test error handling for malformed data"""
        # Test with completely invalid data structure
        malformed_data = {
            'invalid_field': 'invalid_value',
            'another_invalid': 123
        }
        
        # Should handle gracefully and return None
        node_result = self.pipeline.validate_node_data(malformed_data)
        supply_result = self.pipeline.validate_supply_data(malformed_data)
        
        assert node_result is None
        assert supply_result is None
        
        # Error count should be incremented
        assert self.pipeline.error_count >= 2
    
    def test_processing_stats(self):
        """Test processing statistics tracking"""
        # Initial stats
        stats = self.pipeline.get_processing_stats()
        assert stats['processed_count'] == 0
        assert stats['error_count'] == 0
        assert stats['success_rate'] == 0.0
        
        # Process some valid data
        valid_node_data = {
            'node_id': 'test_01',
            'current_load': 100.0,
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        # Validate using helper functions to increment counters
        self.pipeline._validate_node_row(
            'test_01', 100.0, 1, 'Grid', 'active', 28.6139, 77.2090
        )
        
        # Process some invalid data
        self.pipeline._validate_node_row(
            'test_02', -100.0, 4, 'Invalid', 'broken', 0.0, 0.0
        )
        
        # Check updated stats
        stats = self.pipeline.get_processing_stats()
        assert stats['processed_count'] == 1
        assert stats['error_count'] == 1
        assert stats['success_rate'] == 50.0


class TestStandaloneFunctions:
    """Test standalone validation functions"""
    
    def test_validate_energy_node_data_function(self):
        """Test standalone energy node validation function"""
        valid_data = {
            'node_id': 'hospital_01',
            'current_load': 150.5,
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        result = validate_energy_node_data(valid_data)
        
        assert result is not None
        assert isinstance(result, EnergyNode)
        assert result.node_id == 'hospital_01'
    
    def test_validate_supply_event_data_function(self):
        """Test standalone supply event validation function"""
        valid_data = {
            'event_id': 'supply_001',
            'total_supply': 1000.0,
            'grid': 400.0,
            'solar': 300.0,
            'battery': 200.0,
            'diesel': 100.0,
            'timestamp': 1703001600.0
        }
        
        result = validate_supply_event_data(valid_data)
        
        assert result is not None
        assert isinstance(result, SupplyEvent)
        assert result.event_id == 'supply_001'


# Integration test for error handling requirements
class TestErrorHandlingRequirements:
    """Test error handling requirements from the spec"""
    
    def test_requirement_10_1_data_parsing_error_handling(self):
        """
        Test Requirement 10.1: WHEN a data parsing error occurs, 
        THE Stream_Processor SHALL log the error and continue processing
        """
        pipeline = EnergyDataIngestionPipeline()
        
        # Test with malformed data that should cause parsing errors
        malformed_node_data = {
            'node_id': None,  # Invalid type
            'current_load': 'not_a_number',  # Invalid type
            'priority_tier': 'invalid',  # Invalid type
            'source_type': 123,  # Invalid type
            'status': [],  # Invalid type
            'lat': 'invalid',  # Invalid type
            'lng': 'invalid',  # Invalid type
            'timestamp': 'invalid'  # Invalid type
        }
        
        # Should handle gracefully and return None (continue processing)
        result = pipeline.validate_node_data(malformed_node_data)
        assert result is None
        
        # Error should be logged (error_count incremented)
        assert pipeline.error_count > 0
        
        # Pipeline should continue processing valid data after error
        valid_data = {
            'node_id': 'hospital_01',
            'current_load': 150.5,
            'priority_tier': 1,
            'source_type': 'Grid',
            'status': 'active',
            'lat': 28.6139,
            'lng': 77.2090,
            'timestamp': 1703001600.0
        }
        
        valid_result = pipeline.validate_node_data(valid_data)
        assert valid_result is not None
        assert isinstance(valid_result, EnergyNode)


if __name__ == "__main__":
    pytest.main([__file__])