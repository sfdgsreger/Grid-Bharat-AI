#!/usr/bin/env python3
"""
Initialize and populate the vector store for Bharat-Grid AI RAG system
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from rag_system import EnergyRAG, load_historical_data_from_csv, create_sample_patterns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_vector_store():
    """Initialize the vector store with historical data"""
    try:
        logger.info("Initializing Bharat-Grid AI Vector Store...")
        
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found. Using mock embeddings for development.")
            # For development without OpenAI key, we'll create a mock version
            return initialize_mock_vector_store()
        
        # Initialize RAG system
        rag = EnergyRAG(
            vector_store_path="./data/vector_store",
            collection_name="energy_patterns",
            embedding_model="text-embedding-3-small"
        )
        
        # Load historical data from CSV
        historical_csv_path = "./data/historical/sample_consumption_patterns.csv"
        if os.path.exists(historical_csv_path):
            logger.info(f"Loading historical data from {historical_csv_path}")
            patterns_from_csv = load_historical_data_from_csv(historical_csv_path)
            if patterns_from_csv:
                added_count = rag.add_patterns_batch(patterns_from_csv)
                logger.info(f"Added {added_count} patterns from CSV")
        else:
            logger.warning(f"Historical CSV not found at {historical_csv_path}")
        
        # Add sample patterns for testing
        logger.info("Adding sample patterns for testing...")
        sample_patterns = create_sample_patterns()
        sample_count = rag.add_patterns_batch(sample_patterns)
        logger.info(f"Added {sample_count} sample patterns")
        
        # Get and display store statistics
        stats = rag.get_store_stats()
        logger.info(f"Vector store initialized successfully:")
        logger.info(f"  - Total patterns: {stats.get('total_patterns', 0)}")
        logger.info(f"  - Collection: {stats.get('collection_name', 'unknown')}")
        logger.info(f"  - Embedding model: {stats.get('embedding_model', 'unknown')}")
        logger.info(f"  - Store path: {stats.get('store_path', 'unknown')}")
        
        # Test the system with a sample prediction
        logger.info("Testing prediction system...")
        test_prediction(rag)
        
        return rag
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise

def initialize_mock_vector_store():
    """Initialize a mock vector store for development without OpenAI API"""
    logger.info("Initializing mock vector store for development...")
    
    # Create mock data structure
    mock_store_path = "./data/vector_store_mock"
    os.makedirs(mock_store_path, exist_ok=True)
    
    # Create a simple file-based mock store
    mock_patterns_file = os.path.join(mock_store_path, "patterns.json")
    
    import json
    sample_patterns = create_sample_patterns()
    
    # Convert patterns to JSON-serializable format
    patterns_data = []
    for pattern in sample_patterns:
        patterns_data.append({
            "pattern_id": pattern.pattern_id,
            "timestamp": pattern.timestamp,
            "node_id": pattern.node_id,
            "consumption_data": pattern.consumption_data,
            "context": pattern.context,
            "metadata": pattern.metadata
        })
    
    with open(mock_patterns_file, 'w') as f:
        json.dump(patterns_data, f, indent=2)
    
    logger.info(f"Mock vector store created with {len(patterns_data)} patterns")
    logger.info(f"Mock store location: {mock_store_path}")
    
    return None  # Return None to indicate mock mode

def test_prediction(rag: EnergyRAG):
    """Test the prediction system with sample queries"""
    try:
        from rag_system import PredictionRequest
        
        # Test cases
        test_cases = [
            {
                "context": "Hospital experiencing increased patient load during evening hours",
                "node_ids": ["hospital_001"],
                "description": "Hospital evening surge"
            },
            {
                "context": "Factory planning overnight production run with high energy demand",
                "node_ids": ["factory_001"],
                "description": "Factory overnight production"
            },
            {
                "context": "Residential area during monsoon season with potential grid instability",
                "node_ids": ["residential_001"],
                "description": "Residential monsoon scenario"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Test case {i}: {test_case['description']}")
            
            request = PredictionRequest(
                current_context=test_case["context"],
                node_ids=test_case["node_ids"],
                time_horizon=1
            )
            
            start_time = time.time()
            response = rag.generate_prediction(request)
            processing_time = time.time() - start_time
            
            logger.info(f"  - Processing time: {processing_time:.3f}s")
            logger.info(f"  - Confidence: {response.confidence_score:.2f}")
            logger.info(f"  - Similar patterns: {len(response.similar_patterns)}")
            logger.info(f"  - Recommendations: {len(response.optimization_recommendations)}")
            
            # Check if response time meets requirement (<2s)
            if processing_time < 2.0:
                logger.info(f"  ✓ Response time requirement met")
            else:
                logger.warning(f"  ⚠ Response time exceeds 2s requirement")
        
        logger.info("Prediction testing completed successfully")
        
    except Exception as e:
        logger.error(f"Prediction testing failed: {e}")

def main():
    """Main initialization function"""
    try:
        logger.info("Starting Bharat-Grid AI Vector Store Initialization")
        
        # Create necessary directories
        os.makedirs("./data/vector_store", exist_ok=True)
        os.makedirs("./data/historical", exist_ok=True)
        
        # Initialize the vector store
        rag_system = initialize_vector_store()
        
        if rag_system:
            logger.info("Vector store initialization completed successfully")
            logger.info("The RAG system is ready for demand prediction")
        else:
            logger.info("Mock vector store initialized for development")
            logger.info("Set OPENAI_API_KEY environment variable for full functionality")
        
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)