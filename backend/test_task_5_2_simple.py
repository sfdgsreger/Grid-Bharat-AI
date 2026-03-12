# Simple test for Task 5.2 implementation
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from pathway_llm_integration import PathwayRAGSystem, PathwayLLMConfig
from rag_system import PredictionRequest, EnergyRAG, create_sample_patterns

def test_task_5_2_implementation():
    """Test Task 5.2: Pathway LLM Integration"""
    print("Testing Task 5.2: Pathway LLM Integration")
    print("=" * 50)
    
    try:
        # 1. Test Pathway LLM Configuration
        print("\n1. Testing Pathway LLM Configuration...")
        config = PathwayLLMConfig(
            response_timeout=1.8,
            similarity_top_k=5,
            cache_enabled=True
        )
        print(f"   ✓ Config created: {config.embedding_model}")
        
        # 2. Test Pathway RAG System
        print("\n2. Testing Pathway RAG System...")
        pathway_rag = PathwayRAGSystem(config)
        print("   ✓ Pathway RAG system initialized")
        
        # 3. Test Enhanced EnergyRAG with Pathway LLM
        print("\n3. Testing Enhanced EnergyRAG...")
        enhanced_rag = EnergyRAG(
            vector_store_path="./data/vector_store_test_5_2",
            enable_pathway_llm=True
        )
        
        # Add sample patterns
        patterns = create_sample_patterns()
        enhanced_rag.add_patterns_batch(patterns)
        print(f"   ✓ Added {len(patterns)} patterns to vector store")
        
        # 4. Test Prediction Generation
        print("\n4. Testing Prediction Generation...")
        request = PredictionRequest(
            current_context="Hospital experiencing emergency surge with 50% increased patient load",
            time_horizon=2
        )
        
        start_time = time.time()
        response = enhanced_rag.generate_prediction(request)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"   ✓ Response time: {response_time:.3f}s")
        print(f"   ✓ Confidence score: {response.confidence_score:.2f}")
        print(f"   ✓ Similar patterns: {len(response.similar_patterns)}")
        print(f"   ✓ Recommendations: {len(response.optimization_recommendations)}")
        
        # 5. Verify Requirements
        print("\n5. Verifying Task 5.2 Requirements...")
        
        requirements = {
            "Pathway LLM Integration": enhanced_rag.pathway_system is not None,
            "Similarity Search": len(response.similar_patterns) > 0,
            "Prompt Generation": len(response.prediction) > 0,
            "2-Second Response Time": response_time <= 2.0,
            "Optimization Recommendations": len(response.optimization_recommendations) > 0,
            "Confidence Scoring": 0 <= response.confidence_score <= 1
        }
        
        all_passed = True
        for req, status in requirements.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {req}")
            if not status:
                all_passed = False
        
        # 6. Performance Test
        print("\n6. Performance Testing...")
        response_times = []
        
        for i in range(5):
            start = time.time()
            test_response = enhanced_rag.generate_prediction(request)
            end = time.time()
            response_times.append(end - start)
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        print(f"   ✓ Average response time: {avg_time:.3f}s")
        print(f"   ✓ Maximum response time: {max_time:.3f}s")
        
        performance_ok = avg_time <= 2.0 and max_time <= 2.0
        print(f"   {'✅' if performance_ok else '❌'} Performance within 2-second target")
        
        # 7. Test Performance Stats
        print("\n7. Testing Performance Statistics...")
        if enhanced_rag.pathway_system:
            stats = enhanced_rag.pathway_system.get_performance_stats()
            print(f"   ✓ Total predictions: {stats.get('total_predictions', 0)}")
            print(f"   ✓ Cache hit rate: {stats.get('cache_hit_rate', 'N/A')}")
            print(f"   ✓ Target compliance: {stats.get('target_compliance', 'N/A')}")
        
        # Final Result
        print("\n" + "=" * 50)
        if all_passed and performance_ok:
            print("🎉 Task 5.2 Implementation SUCCESSFUL!")
            print("   All requirements met:")
            print("   • Pathway LLM connector integrated")
            print("   • Similarity search implemented")
            print("   • Prompt generation working")
            print("   • 2-second response time achieved")
            print("   • Optimization recommendations generated")
            return True
        else:
            print("⚠️  Task 5.2 Implementation needs attention")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_task_5_2_implementation()
    exit(0 if success else 1)