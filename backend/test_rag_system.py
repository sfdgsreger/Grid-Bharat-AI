#!/usr/bin/env python3
"""
Test suite for the RAG system vector store and embedding functionality
"""

import pytest
import os
import time
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent))

from rag_system import (
    EnergyRAG, 
    ConsumptionPattern, 
    PredictionRequest,
    load_historical_data_from_csv,
    create_sample_patterns
)

class TestEnergyRAG:
    """Test cases for the EnergyRAG system"""
    
    @pytest.fixture
    def temp_vector_store(self):
        """Create a temporary vector store for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing without API calls"""
        with patch('rag_system.OpenAI') as mock_openai:
            # Mock embedding response
            mock_embedding_response = Mock()
            mock_embedding_response.data = [Mock()]
            mock_embedding_response.data[0].embedding = [0.1] * 1536  # Mock 1536-dim embedding
            
            # Mock chat completion response
            mock_chat_response = Mock()
            mock_chat_response.choices = [Mock()]
            mock_chat_response.choices[0].message.content = "Mock prediction response"
            
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_embedding_response
            mock_client.chat.completions.create.return_value = mock_chat_response
            
            mock_openai.return_value = mock_client
            yield mock_client
    
    def test_rag_initialization(self, temp_vector_store, mock_openai_client):
        """Test RAG system initialization"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        assert rag.vector_store_path == temp_vector_store
        assert rag.collection_name == "energy_patterns"
        assert rag.embedding_dimension == 1536
        assert rag.collection is not None
    
    def test_add_single_pattern(self, temp_vector_store, mock_openai_client):
        """Test adding a single consumption pattern"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        pattern = ConsumptionPattern(
            pattern_id="test_pattern_1",
            timestamp=time.time(),
            node_id="hospital_001",
            consumption_data={"current_load": 150.0, "peak_load": 200.0},
            context="Test hospital pattern",
            metadata={"priority_tier": 1, "source_type": "Grid"}
        )
        
        result = rag.add_pattern(pattern)
        assert result is True
        
        # Verify pattern was added
        stats = rag.get_store_stats()
        assert stats["total_patterns"] == 1
    
    def test_add_patterns_batch(self, temp_vector_store, mock_openai_client):
        """Test adding multiple patterns in batch"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        patterns = create_sample_patterns()
        added_count = rag.add_patterns_batch(patterns)
        
        assert added_count == len(patterns)
        
        # Verify all patterns were added
        stats = rag.get_store_stats()
        assert stats["total_patterns"] == len(patterns)
    
    def test_search_similar_patterns(self, temp_vector_store, mock_openai_client):
        """Test similarity search functionality"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Add sample patterns
        patterns = create_sample_patterns()
        rag.add_patterns_batch(patterns)
        
        # Search for similar patterns
        similar_patterns = rag.search_similar_patterns(
            query_context="Hospital during emergency operations",
            k=3
        )
        
        assert len(similar_patterns) <= 3
        assert len(similar_patterns) > 0
        
        # Check that similarity scores are valid
        for pattern in similar_patterns:
            assert 0.0 <= pattern.similarity_score <= 1.0
            assert pattern.pattern_id is not None
            assert pattern.context is not None
    
    def test_search_with_node_filter(self, temp_vector_store, mock_openai_client):
        """Test similarity search with node filtering"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Add sample patterns
        patterns = create_sample_patterns()
        rag.add_patterns_batch(patterns)
        
        # Search with node filter
        similar_patterns = rag.search_similar_patterns(
            query_context="Hospital operations",
            k=5,
            node_filter=["hospital_001"]
        )
        
        # All returned patterns should be from the filtered node
        for pattern in similar_patterns:
            # Note: This test depends on the sample patterns having hospital_001
            assert "hospital" in pattern.pattern_id.lower() or "hospital_001" in str(pattern.metadata)
    
    def test_generate_prediction(self, temp_vector_store, mock_openai_client):
        """Test demand prediction generation"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Add sample patterns
        patterns = create_sample_patterns()
        rag.add_patterns_batch(patterns)
        
        # Generate prediction
        request = PredictionRequest(
            current_context="Hospital experiencing increased patient load",
            node_ids=["hospital_001"],
            time_horizon=2
        )
        
        start_time = time.time()
        response = rag.generate_prediction(request)
        processing_time = time.time() - start_time
        
        # Verify response structure
        assert response.prediction is not None
        assert 0.0 <= response.confidence_score <= 1.0
        assert isinstance(response.similar_patterns, list)
        assert isinstance(response.optimization_recommendations, list)
        assert response.timestamp > 0
        
        # Verify performance requirement (<2s)
        assert processing_time < 2.0, f"Prediction took {processing_time:.3f}s, exceeds 2s requirement"
    
    def test_prediction_without_patterns(self, temp_vector_store, mock_openai_client):
        """Test prediction generation when no similar patterns exist"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Don't add any patterns
        request = PredictionRequest(
            current_context="Unknown scenario with no historical data",
            time_horizon=1
        )
        
        response = rag.generate_prediction(request)
        
        # Should return fallback response
        assert response.prediction is not None
        assert response.confidence_score < 0.5  # Low confidence expected
        assert len(response.similar_patterns) == 0
        assert len(response.optimization_recommendations) > 0
    
    def test_store_persistence(self, temp_vector_store, mock_openai_client):
        """Test that vector store persists data across restarts"""
        # First RAG instance
        rag1 = EnergyRAG(vector_store_path=temp_vector_store)
        patterns = create_sample_patterns()
        rag1.add_patterns_batch(patterns)
        
        initial_count = rag1.get_store_stats()["total_patterns"]
        assert initial_count > 0
        
        # Create second RAG instance with same path
        rag2 = EnergyRAG(vector_store_path=temp_vector_store)
        persisted_count = rag2.get_store_stats()["total_patterns"]
        
        # Data should persist
        assert persisted_count == initial_count
    
    def test_clear_store(self, temp_vector_store, mock_openai_client):
        """Test clearing the vector store"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Add patterns
        patterns = create_sample_patterns()
        rag.add_patterns_batch(patterns)
        
        # Verify patterns exist
        assert rag.get_store_stats()["total_patterns"] > 0
        
        # Clear store
        result = rag.clear_store()
        assert result is True
        
        # Verify store is empty
        assert rag.get_store_stats()["total_patterns"] == 0
    
    def test_error_handling_without_openai_key(self, temp_vector_store):
        """Test error handling when OpenAI API key is not available"""
        # Temporarily remove API key
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        try:
            # This should handle the missing API key gracefully
            rag = EnergyRAG(vector_store_path=temp_vector_store)
            
            # Try to add a pattern (should fail gracefully)
            pattern = ConsumptionPattern(
                pattern_id="test_pattern",
                timestamp=time.time(),
                node_id="test_node",
                consumption_data={"current_load": 100.0},
                context="Test pattern",
                metadata={}
            )
            
            # This should not crash the system
            result = rag.add_pattern(pattern)
            # Result might be False due to API error, but shouldn't crash
            
        finally:
            # Restore API key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

class TestUtilityFunctions:
    """Test utility functions for data loading"""
    
    def test_create_sample_patterns(self):
        """Test sample pattern creation"""
        patterns = create_sample_patterns()
        
        assert len(patterns) > 0
        
        for pattern in patterns:
            assert isinstance(pattern, ConsumptionPattern)
            assert pattern.pattern_id is not None
            assert pattern.node_id is not None
            assert pattern.timestamp > 0
            assert isinstance(pattern.consumption_data, dict)
            assert pattern.context is not None
    
    def test_load_historical_data_from_csv(self):
        """Test loading historical data from CSV"""
        # Create a temporary CSV file
        csv_content = """node_id,timestamp,current_load,peak_load,avg_load,priority_tier,source_type,status,lat,lng
hospital_001,1703001600,150.5,200.0,140.2,1,Grid,active,28.6139,77.2090
factory_001,1703005200,320.5,400.0,300.8,2,Grid,active,28.4595,77.0266"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            patterns = load_historical_data_from_csv(csv_path)
            
            assert len(patterns) == 2
            
            # Check first pattern
            pattern1 = patterns[0]
            assert pattern1.node_id == "hospital_001"
            assert pattern1.consumption_data["current_load"] == 150.5
            assert pattern1.metadata["priority_tier"] == 1
            
            # Check second pattern
            pattern2 = patterns[1]
            assert pattern2.node_id == "factory_001"
            assert pattern2.consumption_data["current_load"] == 320.5
            assert pattern2.metadata["priority_tier"] == 2
            
        finally:
            os.unlink(csv_path)
    
    def test_load_nonexistent_csv(self):
        """Test loading from non-existent CSV file"""
        patterns = load_historical_data_from_csv("nonexistent_file.csv")
        assert patterns == []

class TestPerformanceRequirements:
    """Test performance requirements from the specification"""
    
    def test_prediction_response_time(self, temp_vector_store, mock_openai_client):
        """Test that predictions are generated within 2 seconds (Requirement 3.4)"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Add patterns for realistic test
        patterns = create_sample_patterns()
        rag.add_patterns_batch(patterns)
        
        request = PredictionRequest(
            current_context="Hospital during peak operations",
            time_horizon=1
        )
        
        # Measure response time
        start_time = time.time()
        response = rag.generate_prediction(request)
        processing_time = time.time() - start_time
        
        # Verify requirement: <2s response time
        assert processing_time < 2.0, f"Prediction took {processing_time:.3f}s, exceeds 2s requirement"
        assert response.prediction is not None
    
    def test_knn_index_dimensionality(self, temp_vector_store, mock_openai_client):
        """Test that KNN index uses 1536 dimensions for OpenAI embeddings (Requirement 11.3)"""
        rag = EnergyRAG(vector_store_path=temp_vector_store)
        
        # Verify embedding dimension configuration
        assert rag.embedding_dimension == 1536
        assert rag.embedding_model == "text-embedding-3-small"
    
    def test_vector_store_persistence(self, temp_vector_store, mock_openai_client):
        """Test that embeddings persist across system restarts (Requirement 11.5)"""
        # Create first instance and add data
        rag1 = EnergyRAG(vector_store_path=temp_vector_store)
        patterns = create_sample_patterns()
        rag1.add_patterns_batch(patterns)
        
        original_count = rag1.get_store_stats()["total_patterns"]
        
        # Simulate system restart by creating new instance
        rag2 = EnergyRAG(vector_store_path=temp_vector_store)
        persisted_count = rag2.get_store_stats()["total_patterns"]
        
        # Data should persist
        assert persisted_count == original_count
        assert persisted_count > 0

# Integration test
def test_full_rag_workflow(temp_vector_store, mock_openai_client):
    """Test complete RAG workflow from data loading to prediction"""
    rag = EnergyRAG(vector_store_path=temp_vector_store)
    
    # 1. Load historical data
    patterns = create_sample_patterns()
    added_count = rag.add_patterns_batch(patterns)
    assert added_count > 0
    
    # 2. Search for similar patterns
    similar_patterns = rag.search_similar_patterns(
        query_context="Hospital emergency operations",
        k=3
    )
    assert len(similar_patterns) > 0
    
    # 3. Generate prediction
    request = PredictionRequest(
        current_context="Hospital experiencing surge in critical patients",
        node_ids=["hospital_001"],
        time_horizon=2
    )
    
    response = rag.generate_prediction(request)
    
    # Verify complete workflow
    assert response.prediction is not None
    assert len(response.similar_patterns) > 0
    assert len(response.optimization_recommendations) > 0
    assert response.confidence_score > 0
    assert response.timestamp > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])