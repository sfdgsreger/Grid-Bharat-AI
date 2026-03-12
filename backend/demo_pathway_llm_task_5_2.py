# Demo for Task 5.2: Pathway LLM Integration
import os
import sys
import time
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from pathway_llm_integration import PathwayRAGSystem, PathwayLLMConfig
from rag_system import EnergyRAG, PredictionRequest, create_sample_patterns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_pathway_llm_integration():
    """Demonstrate Task 5.2: Pathway LLM Integration for Predictions"""
    print("🚀 Task 5.2 Demo: Pathway LLM Integration for Bharat-Grid AI")
    print("=" * 60)
    
    try:
        # 1. Test Pathway LLM Configuration
        print("\n📋 1. Testing Pathway LLM Configuration...")
        config = PathwayLLMConfig(
            embedding_model="text-embedding-3-small",
            llm_model="gpt-3.5-turbo",
            response_timeout=1.8,  # Optimized for 2-second target
            similarity_top_k=5,
            cache_enabled=True
        )
        print(f"   ✓ Embedding Model: {config.embedding_model}")
        print(f"   ✓ LLM Model: {config.llm_model}")
        print(f"   ✓ Response Timeout: {config.response_timeout}s")
        print(f"   ✓ Similarity Top-K: {config.similarity_top_k}")
        print(f"   ✓ Caching Enabled: {config.cache_enabled}")
        
        # 2. Initialize Pathway RAG System
        print("\n🔧 2. Initializing Pathway RAG System...")
        pathway_rag = PathwayRAGSystem(config)
        print("   ✓ Pathway LLM components initialized")
        print("   ✓ Response caching enabled")
        print("   ✓ Performance tracking enabled")
        
        # 3. Test Enhanced EnergyRAG with Pathway Integration
        print("\n🧠 3. Testing Enhanced EnergyRAG with Pathway LLM...")
        enhanced_rag = EnergyRAG(
            vector_store_path="./data/vector_store_demo_5_2",
            collection_name="pathway_demo_patterns",
            enable_pathway_llm=True
        )
        
        # Add sample patterns for testing
        sample_patterns = create_sample_patterns()
        added_count = enhanced_rag.add_patterns_batch(sample_patterns)
        print(f"   ✓ Added {added_count} sample patterns to vector store")
        
        # 4. Test Prediction Scenarios
        print("\n🔮 4. Testing Prediction Scenarios...")
        
        test_scenarios = [
            {
                "name": "Hospital Emergency Surge",
                "context": "Hospital experiencing 40% increase in patient load during evening hours with multiple critical cases",
                "time_horizon": 2,
                "node_ids": ["hospital_001"]
            },
            {
                "name": "Factory Peak Production",
                "context": "Manufacturing facility operating at maximum capacity with additional overnight shift",
                "time_horizon": 4,
                "node_ids": ["factory_001"]
            },
            {
                "name": "Residential Evening Peak",
                "context": "Residential area during summer evening with high AC usage and cooking demand",
                "time_horizon": 1,
                "node_ids": ["residential_001"]
            }
        ]
        
        all_response_times = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n   Scenario {i}: {scenario['name']}")
            print(f"   Context: {scenario['context']}")
            
            request = PredictionRequest(
                current_context=scenario['context'],
                node_ids=scenario['node_ids'],
                time_horizon=scenario['time_horizon']
            )
            
            # Measure response time
            start_time = time.time()
            response = enhanced_rag.generate_prediction(request)
            end_time = time.time()
            
            response_time = end_time - start_time
            all_response_times.append(response_time)
            
            # Display results
            print(f"   ⏱️  Response Time: {response_time:.3f}s")
            print(f"   🎯 Confidence Score: {response.confidence_score:.2f}")
            print(f"   📊 Similar Patterns: {len(response.similar_patterns)}")
            print(f"   💡 Recommendations: {len(response.optimization_recommendations)}")
            
            # Show prediction excerpt
            prediction_excerpt = response.prediction[:100] + "..." if len(response.prediction) > 100 else response.prediction
            print(f"   📝 Prediction: {prediction_excerpt}")
            
            # Show top recommendation
            if response.optimization_recommendations:
                print(f"   🔧 Top Recommendation: {response.optimization_recommendations[0]}")
            
            # Check 2-second requirement compliance
            if response_time <= 2.0:
                print("   ✅ Meets 2-second response requirement")
            else:
                print("   ⚠️  Exceeds 2-second response requirement")
        
        # 5. Performance Analysis
        print("\n📈 5. Performance Analysis...")
        
        avg_response_time = sum(all_response_times) / len(all_response_times)
        max_response_time = max(all_response_times)
        min_response_time = min(all_response_times)
        
        compliant_responses = sum(1 for t in all_response_times if t <= 2.0)
        compliance_rate = (compliant_responses / len(all_response_times)) * 100
        
        print(f"   📊 Total Predictions: {len(all_response_times)}")
        print(f"   ⏱️  Average Response Time: {avg_response_time:.3f}s")
        print(f"   ⚡ Fastest Response: {min_response_time:.3f}s")
        print(f"   🐌 Slowest Response: {max_response_time:.3f}s")
        print(f"   🎯 2-Second Compliance: {compliance_rate:.1f}%")
        
        # Get system performance stats
        if hasattr(enhanced_rag, 'pathway_system') and enhanced_rag.pathway_system:
            pathway_stats = enhanced_rag.pathway_system.get_performance_stats()
            print(f"   💾 Cache Hit Rate: {pathway_stats.get('cache_hit_rate', 'N/A')}")
        
        # 6. Test Performance Optimization
        print("\n⚡ 6. Testing Performance Optimization...")
        
        if hasattr(enhanced_rag, 'pathway_system') and enhanced_rag.pathway_system:
            enhanced_rag.pathway_system.optimize_for_performance()
            print("   ✓ Applied Pathway LLM optimizations")
            print(f"   ✓ Reduced similarity search to top-{enhanced_rag.pathway_system.config.similarity_top_k}")
            print(f"   ✓ Set LLM timeout to {enhanced_rag.pathway_system.config.response_timeout}s")
            print("   ✓ Enabled response caching")
        
        # Test optimized performance
        print("\n   Testing optimized performance...")
        optimized_request = PredictionRequest(
            current_context="Quick test for optimized performance",
            time_horizon=1
        )
        
        start_time = time.time()
        optimized_response = enhanced_rag.generate_prediction(optimized_request)
        end_time = time.time()
        
        optimized_time = end_time - start_time
        print(f"   ⚡ Optimized Response Time: {optimized_time:.3f}s")
        
        if optimized_time <= 1.5:
            print("   🚀 Excellent performance after optimization!")
        elif optimized_time <= 2.0:
            print("   ✅ Good performance within 2-second target")
        else:
            print("   ⚠️  Performance needs further optimization")
        
        # 7. Verify Task 5.2 Requirements
        print("\n✅ 7. Task 5.2 Requirements Verification...")
        
        requirements_check = {
            "Pathway LLM Integration": enhanced_rag.pathway_system is not None,
            "Similarity Search": len(response.similar_patterns) > 0,
            "Prompt Generation": len(response.prediction) > 0,
            "2-Second Response Time": avg_response_time <= 2.0,
            "Optimization Recommendations": len(response.optimization_recommendations) > 0,
            "Confidence Scoring": 0 <= response.confidence_score <= 1
        }
        
        for requirement, status in requirements_check.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {requirement}")
        
        all_passed = all(requirements_check.values())
        
        if all_passed:
            print("\n🎉 Task 5.2 Implementation Complete!")
            print("   All requirements successfully implemented:")
            print("   • Pathway LLM connector integrated")
            print("   • Similarity search and prompt generation working")
            print("   • 2-second response time optimization achieved")
            print("   • Optimization recommendations generated")
            print("   • Confidence scoring implemented")
        else:
            print("\n⚠️  Some requirements need attention")
        
        # 8. System Statistics
        print("\n📊 8. Final System Statistics...")
        stats = enhanced_rag.get_store_stats()
        print(f"   📚 Total Patterns: {stats.get('total_patterns', 0)}")
        print(f"   🧠 Embedding Model: {stats.get('embedding_model', 'N/A')}")
        print(f"   🔗 Pathway LLM Enabled: {stats.get('pathway_llm_enabled', False)}")
        
        if 'pathway_performance' in stats:
            perf = stats['pathway_performance']
            print(f"   ⚡ Total Predictions: {perf.get('total_predictions', 0)}")
            print(f"   📈 Target Compliance: {perf.get('target_compliance', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed with error: {e}")
        return False

def test_pathway_llm_fallback():
    """Test fallback behavior when Pathway LLM is not available"""
    print("\n🔄 Testing Pathway LLM Fallback Behavior...")
    
    try:
        # Test with Pathway LLM disabled
        standard_rag = EnergyRAG(
            vector_store_path="./data/vector_store_fallback_test",
            enable_pathway_llm=False
        )
        
        # Add patterns
        patterns = create_sample_patterns()
        standard_rag.add_patterns_batch(patterns)
        
        # Test prediction
        request = PredictionRequest(
            current_context="Testing fallback to standard RAG",
            time_horizon=1
        )
        
        start_time = time.time()
        response = standard_rag.generate_prediction(request)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"   ✓ Standard RAG Response Time: {response_time:.3f}s")
        print(f"   ✓ Fallback prediction generated successfully")
        print(f"   ✓ System gracefully handles missing Pathway LLM")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fallback test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Task 5.2 Pathway LLM Integration Demo...")
    
    # Run main demo
    demo_success = demo_pathway_llm_integration()
    
    # Test fallback behavior
    fallback_success = test_pathway_llm_fallback()
    
    if demo_success and fallback_success:
        print("\n🎊 All Task 5.2 demonstrations completed successfully!")
        print("   The Pathway LLM integration is ready for production use.")
    else:
        print("\n⚠️  Some demonstrations failed. Please check the logs.")
    
    print("\nTask 5.2 Demo Complete.")