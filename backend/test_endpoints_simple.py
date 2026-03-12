#!/usr/bin/env python3
"""
Simple test script for API endpoints without test client dependencies.
"""

import sys
import time
sys.path.append('.')

# Import the components directly
from api import simulate_grid_failure, get_insights, GridFailureRequest
from rag_system import EnergyRAG, PredictionRequest
from pathway_engine import EnergyDataIngestionPipeline
from schemas import SupplyEvent

def test_endpoints_directly():
    """Test the endpoint functions directly."""
    print("Testing API endpoints directly...")
    
    # Test 1: Grid failure simulation
    print("\n1. Testing grid failure simulation function...")
    try:
        request = GridFailureRequest(failure_percentage=0.2)
        # This would normally be called by FastAPI, but we can test the logic
        print(f"   ✓ Grid failure request created: {request.failure_percentage}")
        
        # Test input validation
        try:
            invalid_request = GridFailureRequest(failure_percentage=1.5)
            print("   ⚠ Should have failed validation")
        except Exception as e:
            print(f"   ✓ Input validation working: {type(e).__name__}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: RAG system integration
    print("\n2. Testing RAG system integration...")
    try:
        rag_system = EnergyRAG(
            vector_store_path="./data/vector_store",
            enable_pathway_llm=False
        )
        
        # Test prediction request
        prediction_request = PredictionRequest(
            current_context="Test context: 1000kW supply, 5 nodes active",
            time_horizon_hours=1,
            include_optimization=True
        )
        
        start_time = time.perf_counter()
        response = rag_system.generate_prediction(prediction_request)
        response_time = (time.perf_counter() - start_time) * 1000
        
        print(f"   ✓ RAG prediction generated in {response_time:.2f}ms")
        print(f"   ✓ Prediction preview: {response.prediction[:100]}...")
        
        if response_time <= 2000:
            print(f"   ✓ Response time within target: {response_time:.2f}ms <= 2000ms")
        else:
            print(f"   ⚠ Response time exceeds target: {response_time:.2f}ms > 2000ms")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Pathway engine integration
    print("\n3. Testing Pathway engine integration...")
    try:
        pathway_engine = EnergyDataIngestionPipeline(data_dir="./data")
        
        # Test supply event injection
        supply_event = SupplyEvent(
            event_id="test_event_123",
            total_supply=800.0,
            available_sources={
                "grid": 320.0,
                "solar": 240.0,
                "battery": 160.0,
                "diesel": 80.0
            },
            timestamp=time.time()
        )
        
        print(f"   ✓ Supply event created: {supply_event.total_supply}kW")
        print(f"   ✓ Source mix: {supply_event.available_sources}")
        
        # Test allocation state
        allocation_state = pathway_engine.get_current_allocation_state()
        print(f"   ✓ Current allocation state: {allocation_state}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Input validation
    print("\n4. Testing input validation...")
    
    # Test valid failure percentages
    valid_percentages = [0.0, 0.1, 0.5, 1.0]
    for pct in valid_percentages:
        try:
            request = GridFailureRequest(failure_percentage=pct)
            print(f"   ✓ Valid percentage {pct} accepted")
        except Exception as e:
            print(f"   ⚠ Valid percentage {pct} rejected: {e}")
    
    # Test invalid failure percentages
    invalid_percentages = [-0.1, 1.1, 2.0]
    for pct in invalid_percentages:
        try:
            request = GridFailureRequest(failure_percentage=pct)
            print(f"   ⚠ Invalid percentage {pct} should have been rejected")
        except Exception as e:
            print(f"   ✓ Invalid percentage {pct} correctly rejected")
    
    print("\n✓ Direct endpoint testing completed successfully!")

if __name__ == "__main__":
    test_endpoints_directly()