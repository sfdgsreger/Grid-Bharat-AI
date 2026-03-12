# Pathway LLM Integration for Bharat-Grid AI
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Mock Pathway LLM imports for development/testing
try:
    import pathway as pw
    from pathway.xpacks.llm import embedders, llms, prompts
    from pathway.xpacks.llm.vector_store import VectorStoreServer
    PATHWAY_LLM_AVAILABLE = True
except ImportError:
    # Mock implementations for development
    PATHWAY_LLM_AVAILABLE = False
    
    class MockEmbedder:
        def __init__(self, model="text-embedding-3-small", **kwargs):
            self.model = model
        
        def __call__(self, text: str) -> List[float]:
            # Generate deterministic mock embedding
            import hashlib
            import numpy as np
            text_hash = hashlib.md5(text.encode()).hexdigest()
            np.random.seed(int(text_hash[:8], 16))
            return np.random.normal(0, 1, 1536).tolist()
    
    class MockLLMChat:
        def __init__(self, model="gpt-3.5-turbo", **kwargs):
            self.model = model
        
        def __call__(self, prompt: str, timeout: float = None) -> str:
            # Generate mock prediction based on prompt content
            if "hospital" in prompt.lower():
                return "Predicted demand: 180-220kW for hospital operations. High confidence based on similar emergency patterns. Monitor critical systems closely."
            elif "factory" in prompt.lower():
                return "Predicted demand: 280-350kW for factory operations. Moderate confidence based on production patterns. Optimize for peak efficiency."
            else:
                return "Predicted demand: 120-150kW based on historical patterns. Standard confidence level. Monitor for variations."
    
    class MockPromptTemplate:
        def __init__(self, template: str):
            self.template = template
        
        def format(self, **kwargs) -> str:
            return self.template.format(**kwargs)
    
    # Mock modules
    class MockEmbedders:
        OpenAIEmbedder = MockEmbedder
        
        @staticmethod
        def ExponentialBackoffRetryStrategy(**kwargs):
            return None
    
    class MockLLMs:
        OpenAIChat = MockLLMChat
        
        @staticmethod
        def ExponentialBackoffRetryStrategy(**kwargs):
            return None
    
    class MockPrompts:
        PromptTemplate = MockPromptTemplate
    
    embedders = MockEmbedders()
    llms = MockLLMs()
    prompts = MockPrompts()

from pydantic import BaseModel, Field

# Import types without circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rag_system import ConsumptionPattern, SimilarPattern, PredictionRequest, PredictionResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PathwayLLMConfig(BaseModel):
    """Configuration for Pathway LLM integration"""
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    llm_model: str = Field(default="gpt-3.5-turbo", description="OpenAI LLM model")
    vector_dimension: int = Field(default=1536, description="Embedding vector dimension")
    similarity_top_k: int = Field(default=5, description="Number of similar patterns to retrieve")
    response_timeout: float = Field(default=1.8, description="LLM response timeout in seconds")
    cache_enabled: bool = Field(default=True, description="Enable response caching")

class PathwayRAGSystem:
    """Pathway-based RAG System for Energy Demand Prediction"""
    
    def __init__(self, config: PathwayLLMConfig = None):
        """Initialize Pathway LLM integration"""
        self.config = config or PathwayLLMConfig()
        
        # Initialize Pathway LLM components
        self._initialize_pathway_components()
        
        # Performance tracking
        self.response_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info("PathwayRAGSystem initialized with Pathway LLM integration")
    
    def _initialize_pathway_components(self):
        """Initialize Pathway LLM embedder and chat components"""
        try:
            # Initialize embedder
            self.embedder = embedders.OpenAIEmbedder(
                model=self.config.embedding_model,
                retry_strategy=embedders.ExponentialBackoffRetryStrategy(max_retries=3)
            )
            
            # Initialize LLM chat
            self.llm_chat = llms.OpenAIChat(
                model=self.config.llm_model,
                retry_strategy=llms.ExponentialBackoffRetryStrategy(max_retries=3),
                temperature=0.3,
                max_tokens=500
            )
            
            # Initialize prompt template
            self.prompt_template = prompts.PromptTemplate(
                template="""Based on the following historical energy consumption patterns, predict the energy demand for the next {time_horizon} hour(s).

Current Context: {current_context}

Historical Patterns:
{patterns_context}

Please provide:
1. Predicted energy demand in kW
2. Key factors influencing the prediction  
3. Confidence level and reasoning
4. Potential risks or anomalies to watch for

Keep the response concise and actionable for grid operators."""
            )
            
            # Response cache for optimization
            self.response_cache = {} if self.config.cache_enabled else None
            
            logger.info("Pathway LLM components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pathway components: {e}")
            raise
    
    def create_pathway_pipeline(self, patterns_table=None):
        """Create Pathway pipeline for real-time RAG processing (mock implementation)"""
        try:
            if not PATHWAY_LLM_AVAILABLE:
                logger.info("Using mock Pathway pipeline for development")
                return None
            
            # Real Pathway implementation would go here
            # embedded_patterns = patterns_table.select(
            #     pattern_id=pw.this.pattern_id,
            #     context=pw.this.context,
            #     consumption_data=pw.this.consumption_data,
            #     metadata=pw.this.metadata,
            #     embedding=self.embedder(pw.this.context)
            # )
            
            logger.info("Pathway pipeline created for RAG processing")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create Pathway pipeline: {e}")
            raise
    
    def similarity_search_pathway(self, 
                                query_context: str, 
                                patterns_table=None,
                                k: int = None) -> List[Dict[str, Any]]:
        """Perform similarity search using Pathway vector operations"""
        try:
            start_time = time.time()
            k = k or self.config.similarity_top_k
            
            # Generate query embedding
            query_embedding = self.embedder(query_context)
            
            # Mock similarity search results for development
            # In production, this would use Pathway's vector store server
            mock_patterns = [
                {
                    "pattern_id": "pathway_pattern_1",
                    "similarity_score": 0.85,
                    "context": "Hospital during peak hours with high demand",
                    "consumption_data": {"current_load": 180.0, "peak_load": 220.0},
                    "metadata": {"priority_tier": 1, "source_type": "Grid"}
                },
                {
                    "pattern_id": "pathway_pattern_2", 
                    "similarity_score": 0.78,
                    "context": "Factory operating at full capacity",
                    "consumption_data": {"current_load": 320.0, "peak_load": 380.0},
                    "metadata": {"priority_tier": 2, "source_type": "Grid"}
                },
                {
                    "pattern_id": "pathway_pattern_3",
                    "similarity_score": 0.72,
                    "context": "Residential area during evening peak consumption",
                    "consumption_data": {"current_load": 95.0, "peak_load": 120.0},
                    "metadata": {"priority_tier": 3, "source_type": "Grid"}
                }
            ]
            
            similar_patterns = []
            for pattern_data in mock_patterns[:k]:
                # Import here to avoid circular dependency
                from rag_system import SimilarPattern
                similar_patterns.append(SimilarPattern(
                    pattern_id=pattern_data["pattern_id"],
                    similarity_score=pattern_data["similarity_score"],
                    context=pattern_data["context"],
                    consumption_data=pattern_data["consumption_data"],
                    metadata=pattern_data["metadata"]
                ))
            
            search_time = time.time() - start_time
            logger.debug(f"Pathway similarity search completed in {search_time:.3f}s")
            
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Pathway similarity search failed: {e}")
            return []
    
    def generate_prediction_pathway(self, request) -> Dict[str, Any]:
        """Generate prediction using Pathway LLM with 2-second optimization"""
        try:
            # Import here to avoid circular dependency
            from rag_system import PredictionResponse
            
            start_time = time.time()
            
            # Check cache first for optimization
            cache_key = f"{request.current_context}_{request.time_horizon}"
            if self.response_cache and cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                if time.time() - cached_response["timestamp"] < 300:  # 5-minute cache
                    self.cache_hits += 1
                    logger.debug("Returning cached prediction")
                    return cached_response["response"]
            
            self.cache_misses += 1
            
            # Perform similarity search (optimized for speed)
            similar_patterns = self.similarity_search_pathway(
                query_context=request.current_context,
                patterns_table=None,  # Would be actual patterns table in production
                k=3  # Reduced for speed optimization
            )
            
            # Generate prediction using Pathway LLM
            if similar_patterns:
                prediction_text = self._generate_pathway_llm_prediction(
                    current_context=request.current_context,
                    similar_patterns=similar_patterns,
                    time_horizon=request.time_horizon
                )
                confidence_score = min(0.9, sum(p.similarity_score for p in similar_patterns) / len(similar_patterns))
            else:
                prediction_text = "Insufficient historical data for accurate prediction. Using baseline demand estimation."
                confidence_score = 0.2
            
            # Generate optimization recommendations
            recommendations = self._generate_pathway_recommendations(similar_patterns)
            
            # Create response
            response = PredictionResponse(
                prediction=prediction_text,
                similar_patterns=similar_patterns,
                confidence_score=confidence_score,
                optimization_recommendations=recommendations,
                timestamp=time.time()
            )
            
            # Cache response for optimization
            if self.response_cache:
                self.response_cache[cache_key] = {
                    "response": response,
                    "timestamp": time.time()
                }
            
            # Track performance
            total_time = time.time() - start_time
            self.response_times.append(total_time)
            
            # Log performance warning if exceeding 2-second target
            if total_time > 2.0:
                logger.warning(f"Prediction response time {total_time:.3f}s exceeds 2s target")
            else:
                logger.info(f"Pathway prediction generated in {total_time:.3f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Pathway prediction generation failed: {e}")
            # Return fallback response
            from rag_system import PredictionResponse
            return PredictionResponse(
                prediction="System error occurred. Using conservative demand estimates.",
                similar_patterns=[],
                confidence_score=0.0,
                optimization_recommendations=["Check system status", "Verify data connectivity"],
                timestamp=time.time()
            )
    
    def _generate_pathway_llm_prediction(self, 
                                       current_context: str,
                                       similar_patterns: List[Any],
                                       time_horizon: int) -> str:
        """Generate prediction using Pathway LLM with timeout optimization"""
        try:
            # Prepare patterns context (optimized for token efficiency)
            patterns_context = []
            for i, pattern in enumerate(similar_patterns[:3], 1):  # Limit to top 3 for speed
                patterns_context.append(
                    f"Pattern {i} (sim: {pattern.similarity_score:.2f}): {pattern.context} | "
                    f"Load: {pattern.consumption_data.get('current_load', 0):.0f}kW"
                )
            
            patterns_text = "\n".join(patterns_context)
            
            # Generate prompt using Pathway template
            prompt_vars = {
                "current_context": current_context,
                "time_horizon": time_horizon,
                "patterns_context": patterns_text
            }
            
            formatted_prompt = self.prompt_template.format(**prompt_vars)
            
            # Call Pathway LLM with timeout
            start_llm_time = time.time()
            
            # Use Pathway LLM chat with timeout optimization
            response = self.llm_chat(
                formatted_prompt,
                timeout=self.config.response_timeout
            )
            
            llm_time = time.time() - start_llm_time
            logger.debug(f"Pathway LLM response generated in {llm_time:.3f}s")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Pathway LLM prediction failed: {e}")
            # Return optimized fallback
            avg_load = sum(p.consumption_data.get('current_load', 0) for p in similar_patterns) / max(len(similar_patterns), 1)
            return f"Based on {len(similar_patterns)} patterns, predicted demand: {avg_load * 1.1:.0f}kW for next {time_horizon}h. Monitor for variations."
    
    def _generate_pathway_recommendations(self, similar_patterns: List[Any]) -> List[str]:
        """Generate optimization recommendations using Pathway analysis"""
        recommendations = []
        
        if not similar_patterns:
            return [
                "Insufficient pattern data - use conservative allocation",
                "Monitor real-time consumption closely",
                "Prepare backup power sources"
            ]
        
        # Analyze pattern characteristics
        avg_similarity = sum(p.similarity_score for p in similar_patterns) / len(similar_patterns)
        avg_load = sum(p.consumption_data.get('current_load', 0) for p in similar_patterns) / len(similar_patterns)
        
        # Generate targeted recommendations
        if avg_similarity > 0.8:
            recommendations.append("High pattern confidence - predictions are reliable")
        elif avg_similarity > 0.6:
            recommendations.append("Moderate pattern match - monitor for deviations")
        else:
            recommendations.append("Low pattern similarity - use conservative estimates")
        
        if avg_load > 200:
            recommendations.append("High demand predicted - ensure adequate supply reserves")
        elif avg_load > 100:
            recommendations.append("Moderate demand - optimize source mix for efficiency")
        else:
            recommendations.append("Low demand period - opportunity for maintenance")
        
        # Add priority-based recommendations
        has_hospital = any(p.metadata.get('priority_tier') == 1 for p in similar_patterns)
        if has_hospital:
            recommendations.append("Critical infrastructure detected - prioritize tier 1 nodes")
        
        return recommendations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the Pathway LLM system"""
        if not self.response_times:
            return {"status": "no_data"}
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        max_response_time = max(self.response_times)
        min_response_time = min(self.response_times)
        
        # Calculate percentage within 2-second target
        within_target = sum(1 for t in self.response_times if t <= 2.0)
        target_percentage = (within_target / len(self.response_times)) * 100
        
        return {
            "total_predictions": len(self.response_times),
            "avg_response_time": round(avg_response_time, 3),
            "max_response_time": round(max_response_time, 3),
            "min_response_time": round(min_response_time, 3),
            "target_compliance": f"{target_percentage:.1f}%",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": f"{(self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 100:.1f}%"
        }
    
    def optimize_for_performance(self):
        """Apply performance optimizations for 2-second target"""
        try:
            # Reduce similarity search results for speed
            self.config.similarity_top_k = min(self.config.similarity_top_k, 3)
            
            # Reduce LLM timeout for faster responses
            self.config.response_timeout = min(self.config.response_timeout, 1.5)
            
            # Enable caching if not already enabled
            if not self.config.cache_enabled:
                self.config.cache_enabled = True
                self.response_cache = {}
            
            # Clear old cache entries (keep only recent ones)
            if self.response_cache:
                current_time = time.time()
                expired_keys = [
                    key for key, value in self.response_cache.items()
                    if current_time - value["timestamp"] > 300  # 5 minutes
                ]
                for key in expired_keys:
                    del self.response_cache[key]
            
            logger.info("Performance optimizations applied for 2-second target")
            
        except Exception as e:
            logger.error(f"Failed to apply performance optimizations: {e}")

# Integration functions for backward compatibility

def create_pathway_rag_system(config: PathwayLLMConfig = None) -> PathwayRAGSystem:
    """Create and initialize Pathway RAG system"""
    return PathwayRAGSystem(config)

def integrate_with_existing_rag(existing_rag, pathway_config: PathwayLLMConfig = None):
    """Integrate Pathway LLM with existing RAG system"""
    try:
        pathway_rag = PathwayRAGSystem(pathway_config)
        
        # Add method to existing RAG for Pathway predictions
        def generate_pathway_prediction(request: PredictionRequest) -> PredictionResponse:
            return pathway_rag.generate_prediction_pathway(request)
        
        # Monkey patch the existing RAG system
        existing_rag.generate_pathway_prediction = generate_pathway_prediction
        existing_rag.pathway_system = pathway_rag
        
        logger.info("Pathway LLM integration added to existing RAG system")
        return existing_rag
        
    except Exception as e:
        logger.error(f"Failed to integrate Pathway LLM: {e}")
        return existing_rag

# Example usage and testing
if __name__ == "__main__":
    # Test Pathway LLM integration
    config = PathwayLLMConfig(
        response_timeout=1.8,
        similarity_top_k=3,
        cache_enabled=True
    )
    
    pathway_rag = PathwayRAGSystem(config)
    
    # Test prediction
    request = PredictionRequest(
        current_context="Hospital experiencing surge in patient load during evening peak hours",
        time_horizon=2
    )
    
    print("Testing Pathway LLM integration...")
    start_time = time.time()
    
    response = pathway_rag.generate_prediction_pathway(request)
    
    total_time = time.time() - start_time
    print(f"Prediction generated in {total_time:.3f}s")
    print(f"Prediction: {response.prediction}")
    print(f"Confidence: {response.confidence_score:.2f}")
    print(f"Similar patterns: {len(response.similar_patterns)}")
    
    # Show performance stats
    stats = pathway_rag.get_performance_stats()
    print(f"Performance stats: {stats}")