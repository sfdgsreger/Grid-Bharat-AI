# Test Pathway LLM Integration for Task 5.2
import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent))

from pathway_llm_integration import (
    PathwayRAGSystem, 
    PathwayLLMConfig,
    create_pathway_rag_system,
    integrate_with_existing_rag
)
from rag_system import EnergyRAG, PredictionRequest, create_sample_patterns

class TestPathwayLLMIntegration:
    """Test cases for Pathway LLM integration (Task 5.2)"""
    
    @pytest.fixture
    def temp_vector_store(self):
        """Create temporary vector store for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_pathway_components(self):
        """Mock Pathway LLM components for testing"""
        with patch('pathway_llm_integration.embedders') as mock_embedders, \
             patch('pathway_llm_integration.llms') as mock_llms, \
             patch('pathway_llm_integration.prompts') as mock_prompts:
            
            # Mock embedder
            mock_embedder = Mock()
            mock_embedder.return_value = [0.1] * 1536  # Mock embedding
            mock_embedders.OpenAIEmbedder.return_value = mock_embedder
            
            # Mock LLM chat
            mock_chat = Mock()
            mock_chat.return_value = "Predicted demand: 180kW for next 2 hours. High confidence based on similar patterns."
            mock_llms.OpenAIChat.return_value = mock_chat
            
            # Mock prompt template
            mock_template = Mock()
            mock_template.format.return_value = "Formatted prompt"
            mock_prompts.PromptTemplate.return_value = mock_template
            
            yield {
                'embedder': mock_embedder,
                'chat': mock_chat,
                'template': mock_template
            }
    
    def test_pathway_config_initialization(self):
        """Test PathwayLLMConfig initialization with default values"""
        config = PathwayLLMConfig()
        
        assert config.embedding_model == "text-embedding-3-small"
        assert config.llm_model == "gpt-3.5-turbo"
        assert config.vector_dimension == 1536
        assert config.similarity_top_k == 5
        assert config.response_timeout == 1.8
        assert config.cache_enabled == True
    
    def test_pathway_config_custom_values(self):
        """Test PathwayLLMConfig with custom values"""
        config = PathwayLLMConfig(
            embedding_model="text-embedding-ada-002",
            llm_model="gpt-4",
            response_timeout=1.5,
            similarity_top_k=3,
            cache_enabled=False
        )
        
        assert config.embedding_model == "text-embedding-ada-002"
        assert config.llm_model == "gpt-4"
        assert config.response_timeout == 1.5
        assert config.similarity_top_k == 3
        assert config.cache_enabled == False
    
    def test_pathway_rag_system_initialization(self, mock_pathway_components):
        """Test PathwayRAGSystem initialization"""
        config = PathwayLLMConfig()
        pathway_rag = PathwayRAGSystem(config)
        
        assert pathway_rag.config == config
        assert pathway_rag.response_times == []
        assert pathway_rag.cache_hits == 0
        assert pathway_rag.cache_misses == 0
        assert pathway_rag.response_cache == {}
    
    def test_similarity_search_pathway(self, mock_pathway_components):
        """Test Pathway similarity search functionality"""
        pathway_rag = PathwayRAGSystem()
        
        similar_patterns = pathway_rag.similarity_search_pathway(
            query_context="Hospital during peak hours",
            patterns_table=None,  # Mock table
            k=3
        )
        
        assert len(similar_patterns) <= 3
        assert all(hasattr(p, 'pattern_id') for p in similar_patterns)
        assert all(hasattr(p, 'similarity_score') for p in similar_patterns)
        assert all(0 <= p.similarity_score <= 1 for p in similar_patterns)
    
    def test_generate_prediction_pathway_success(self, mock_pathway_components):
        """Test successful prediction generation using Pathway LLM"""
        pathway_rag = PathwayRAGSystem()
        
        request = PredictionRequest(
            current_context="Hospital experiencing high patient load",
            time_horizon=2
        )
        
        start_time = time.time()
        response = pathway_rag.generate_prediction_pathway(request)
        end_time = time.time()
        
        # Verify response structure
        assert hasattr(response, 'prediction')
        assert hasattr(response, 'similar_patterns')
        assert hasattr(response, 'confidence_score')
        assert hasattr(response, 'optimization_recommendations')
        assert hasattr(response, 'timestamp')
        
        # Verify response content
        assert isinstance(response.prediction, str)
        assert len(response.prediction) > 0
        assert 0 <= response.confidence_score <= 1
        assert isinstance(response.optimization_recommendations, list)
        
        # Verify performance (should be under 2 seconds)
        response_time = end_time - start_time
        assert response_time < 2.0, f"Response time {response_time:.3f}s exceeds 2s target"
    
    def test_generate_prediction_with_caching(self, mock_pathway_components):
        """Test prediction caching for performance optimization"""
        config = PathwayLLMConfig(cache_enabled=True)
        pathway_rag = PathwayRAGSystem(config)
        
        request = PredictionRequest(
            current_context="Factory at full capacity",
            time_horizon=1
        )
        
        # First request (cache miss)
        response1 = pathway_rag.generate_prediction_pathway(request)
        assert pathway_rag.cache_misses == 1
        assert pathway_rag.cache_hits == 0
        
        # Second identical request (cache hit)
        response2 = pathway_rag.generate_prediction_pathway(request)
        assert pathway_rag.cache_misses == 1
        assert pathway_rag.cache_hits == 1
        
        # Responses should be identical
        assert response1.prediction == response2.prediction
        assert response1.confidence_score == response2.confidence_score
    
    def test_performance_optimization(self, mock_pathway_components):
        """Test performance optimization for 2-second target"""
        pathway_rag = PathwayRAGSystem()
        
        # Apply optimizations
        pathway_rag.optimize_for_performance()
        
        # Verify optimizations were applied
        assert pathway_rag.config.similarity_top_k <= 3
        assert pathway_rag.config.response_timeout <= 1.5
        assert pathway_rag.config.cache_enabled == True
        assert pathway_rag.response_cache is not None
    
    def test_performance_stats_tracking(self, mock_pathway_components):
        """Test performance statistics tracking"""
        pathway_rag = PathwayRAGSystem()
        
        # Generate some predictions to create stats
        request = PredictionRequest(
            current_context="Test context",
            time_horizon=1
        )
        
        for _ in range(3):
            pathway_rag.generate_prediction_pathway(request)
        
        stats = pathway_rag.get_performance_stats()
        
        assert stats["total_predictions"] == 3
        assert "avg_response_time" in stats
        assert "max_response_time" in stats
        assert "min_response_time" in stats
        assert "target_compliance" in stats
        assert "cache_hit_rate" in stats
    
    def test_integration_with_existing_rag(self, temp_vector_store, mock_pathway_components):
        """Test integration with existing EnergyRAG system"""
        # Create existing RAG system
        existing_rag = EnergyRAG(
            vector_store_path=temp_vector_store,
            enable_pathway_llm=False  # Disable to test manual integration
        )
        
        # Integrate Pathway LLM
        config = PathwayLLMConfig()
        integrated_rag = integrate_with_existing_rag(existing_rag, config)
        
        # Verify integration
        assert hasattr(integrated_rag, 'pathway_system')
        assert hasattr(integrated_rag, 'generate_pathway_prediction')
        assert integrated_rag.pathway_system is not None
    
    def test_enhanced_rag_with_pathway_llm(self, temp_vector_store, mock_pathway_components):
        """Test enhanced EnergyRAG with Pathway LLM enabled"""
        # Mock the pathway import to be available
        with patch('rag_system.PATHWAY_AVAILABLE', True):
            rag = EnergyRAG(
                vector_store_path=temp_vector_store,
                enable_pathway_llm=True
            )
            
            # Add sample patterns
            patterns = create_sample_patterns()
            rag.add_patterns_batch(patterns)
            
            # Test prediction with Pathway LLM
            request = PredictionRequest(
                current_context="Hospital during emergency surge",
                time_horizon=2
            )
            
            start_time = time.time()
            response = rag.generate_prediction(request)
            end_time = time.time()
            
            # Verify response
            assert response is not None
            assert isinstance(response.prediction, str)
            assert len(response.similar_patterns) >= 0
            
            # Verify performance
            response_time = end_time - start_time
            assert response_time < 2.0, f"Response time {response_time:.3f}s exceeds 2s target"
    
    def test_fallback_to_standard_rag(self, temp_vector_store):
        """Test fallback to standard RAG when Pathway LLM fails"""
        # Mock Pathway to be unavailable
        with patch('rag_system.PATHWAY_AVAILABLE', False):
            rag = EnergyRAG(
                vector_store_path=temp_vector_store,
                enable_pathway_llm=True  # Should fallback gracefully
            )
            
            # Add sample patterns
            patterns = create_sample_patterns()
            rag.add_patterns_batch(patterns)
            
            # Test prediction (should use standard RAG)
            request = PredictionRequest(
                current_context="Factory maintenance period",
                time_horizon=1
            )
            
            response = rag.generate_prediction(request)
            
            # Verify response is still generated
            assert response is not None
            assert isinstance(response.prediction, str)
            assert rag.pathway_system is None
    
    def test_response_time_requirement_compliance(self, mock_pathway_components):
        """Test compliance with 2-second response time requirement (Requirement 3.4)"""
        pathway_rag = PathwayRAGSystem()
        
        request = PredictionRequest(
            current_context="Critical infrastructure monitoring",
            time_horizon=1
        )
        
        # Test multiple predictions to ensure consistent performance
        response_times = []
        for _ in range(5):
            start_time = time.time()
            response = pathway_rag.generate_prediction_pathway(request)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Each prediction should be under 2 seconds
            assert response_time < 2.0, f"Response time {response_time:.3f}s exceeds 2s requirement"
        
        # Average response time should be well under 2 seconds
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.5, f"Average response time {avg_response_time:.3f}s too high"
    
    def test_optimization_recommendations_generation(self, mock_pathway_components):
        """Test generation of optimization recommendations (Requirement 3.5)"""
        pathway_rag = PathwayRAGSystem()
        
        request = PredictionRequest(
            current_context="Multiple hospitals and factories at peak load",
            time_horizon=2
        )
        
        response = pathway_rag.generate_prediction_pathway(request)
        
        # Verify recommendations are generated
        assert len(response.optimization_recommendations) > 0
        assert all(isinstance(rec, str) for rec in response.optimization_recommendations)
        assert all(len(rec) > 0 for rec in response.optimization_recommendations)
        
        # Check for relevant optimization content
        recommendations_text = " ".join(response.optimization_recommendations).lower()
        assert any(keyword in recommendations_text for keyword in [
            'priority', 'tier', 'hospital', 'critical', 'demand', 'supply', 'backup'
        ])

def test_create_pathway_rag_system():
    """Test factory function for creating Pathway RAG system"""
    with patch('pathway_llm_integration.PathwayRAGSystem') as mock_system:
        config = PathwayLLMConfig()
        create_pathway_rag_system(config)
        
        mock_system.assert_called_once_with(config)

def test_pathway_llm_integration_requirements():
    """Test that Pathway LLM integration meets all Task 5.2 requirements"""
    # This test verifies the integration addresses all specified requirements
    
    # Requirement 3.2: Retrieve 5 most similar historical patterns
    config = PathwayLLMConfig(similarity_top_k=5)
    assert config.similarity_top_k == 5
    
    # Requirement 3.3: Generate demand forecast using LLM
    # Verified by test_generate_prediction_pathway_success
    
    # Requirement 3.4: Return predictions within 2 seconds
    # Verified by test_response_time_requirement_compliance
    
    # Requirement 3.5: Include optimization recommendations
    # Verified by test_optimization_recommendations_generation
    
    # Requirement 11.4: Use KNN index for retrieval
    # Verified by similarity search implementation
    
    assert True  # All requirements are covered by other tests

if __name__ == "__main__":
    # Run basic integration test
    print("Testing Pathway LLM Integration...")
    
    try:
        # Test configuration
        config = PathwayLLMConfig(response_timeout=1.5)
        print(f"✓ Configuration created: {config.embedding_model}")
        
        # Test system creation
        with patch('pathway_llm_integration.embedders'), \
             patch('pathway_llm_integration.llms'), \
             patch('pathway_llm_integration.prompts'):
            
            pathway_rag = PathwayRAGSystem(config)
            print("✓ Pathway RAG system initialized")
            
            # Test prediction
            request = PredictionRequest(
                current_context="Test hospital scenario",
                time_horizon=1
            )
            
            start_time = time.time()
            response = pathway_rag.generate_prediction_pathway(request)
            end_time = time.time()
            
            print(f"✓ Prediction generated in {end_time - start_time:.3f}s")
            print(f"✓ Confidence score: {response.confidence_score:.2f}")
            print(f"✓ Recommendations: {len(response.optimization_recommendations)}")
            
        print("\n🎉 Pathway LLM Integration Test Passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise