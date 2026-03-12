# RAG System for Bharat-Grid AI Demand Prediction
import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings

# OpenAI for embeddings
import openai
from openai import OpenAI

# Pydantic models
from pydantic import BaseModel, Field

# Pathway LLM integration (optional import)
try:
    from pathway_llm_integration import PathwayRAGSystem, PathwayLLMConfig
    PATHWAY_AVAILABLE = True
except ImportError:
    PATHWAY_AVAILABLE = False
    # Logger is defined below, so we'll defer this warning

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsumptionPattern(BaseModel):
    """Historical consumption pattern for embedding"""
    pattern_id: str = Field(..., description="Unique identifier for the pattern")
    timestamp: float = Field(..., description="Unix timestamp of the pattern")
    node_id: str = Field(..., description="Energy node identifier")
    consumption_data: Dict[str, float] = Field(..., description="Consumption metrics")
    context: str = Field(..., description="Contextual description of the pattern")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class SimilarPattern(BaseModel):
    """Similar pattern retrieved from vector store"""
    pattern_id: str
    similarity_score: float
    context: str
    consumption_data: Dict[str, float]
    metadata: Dict[str, Any]

class PredictionRequest(BaseModel):
    """Request for demand prediction"""
    current_context: str = Field(..., description="Current energy context for prediction")
    node_ids: Optional[List[str]] = Field(default=None, description="Specific nodes to predict for")
    time_horizon: int = Field(default=1, description="Prediction horizon in hours")

class PredictionResponse(BaseModel):
    """Response with demand prediction and insights"""
    prediction: str = Field(..., description="AI-generated demand prediction")
    similar_patterns: List[SimilarPattern] = Field(..., description="Retrieved similar patterns")
    confidence_score: float = Field(..., description="Prediction confidence (0-1)")
    optimization_recommendations: List[str] = Field(..., description="Optimization suggestions")
    timestamp: float = Field(..., description="Prediction timestamp")

class EnergyRAG:
    """RAG System for Energy Demand Prediction"""
    
    def __init__(self, 
                 vector_store_path: str = "./data/vector_store",
                 collection_name: str = "energy_patterns",
                 embedding_model: str = "text-embedding-3-small",
                 embedding_dimension: int = 1536,
                 enable_pathway_llm: bool = True):
        """
        Initialize the RAG system with vector store and embedding configuration
        
        Args:
            vector_store_path: Path to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            embedding_model: OpenAI embedding model to use
            embedding_dimension: Dimension of embeddings (1536 for OpenAI)
            enable_pathway_llm: Enable Pathway LLM integration for enhanced performance
        """
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        
        # Initialize OpenAI client (with fallback for development)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            self.use_mock_embeddings = False
        else:
            self.openai_client = None
            self.use_mock_embeddings = True
            logger.warning("OpenAI API key not found. Using mock embeddings for development.")
        
        # Initialize ChromaDB
        self._initialize_vector_store()
        
        # Log Pathway availability after logger is initialized
        if not PATHWAY_AVAILABLE:
            logger.warning("Pathway LLM integration not available. Install pathway[xpack-llm] for enhanced features.")
        
        # Initialize Pathway LLM integration if available and enabled
        self.pathway_system = None
        if enable_pathway_llm and PATHWAY_AVAILABLE:
            try:
                pathway_config = PathwayLLMConfig(
                    embedding_model=embedding_model,
                    vector_dimension=embedding_dimension,
                    response_timeout=1.8,  # Optimized for 2-second target
                    similarity_top_k=5,
                    cache_enabled=True
                )
                self.pathway_system = PathwayRAGSystem(pathway_config)
                logger.info("Pathway LLM integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Pathway LLM: {e}")
                self.pathway_system = None
        
        logger.info(f"EnergyRAG initialized with {embedding_model} embeddings")
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store with persistence"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.vector_store_path, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_store_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            logger.info(f"Vector store initialized at {self.vector_store_path}")
            logger.info(f"Collection '{self.collection_name}' ready with {self.collection.count()} patterns")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI or mock embeddings"""
        try:
            if self.use_mock_embeddings:
                # Generate mock embedding for development
                import hashlib
                import numpy as np
                
                # Create deterministic mock embedding based on text hash
                text_hash = hashlib.md5(text.encode()).hexdigest()
                np.random.seed(int(text_hash[:8], 16))  # Use first 8 chars of hash as seed
                mock_embedding = np.random.normal(0, 1, self.embedding_dimension).tolist()
                return mock_embedding
            else:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero embedding as fallback
            return [0.0] * self.embedding_dimension
    
    def _create_pattern_context(self, pattern: ConsumptionPattern) -> str:
        """Create contextual description for a consumption pattern"""
        context_parts = [
            f"Node {pattern.node_id} consumption pattern",
            f"Timestamp: {datetime.fromtimestamp(pattern.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Context: {pattern.context}"
        ]
        
        # Add consumption metrics
        if pattern.consumption_data:
            metrics = []
            for key, value in pattern.consumption_data.items():
                metrics.append(f"{key}: {value:.2f}kW")
            context_parts.append(f"Metrics: {', '.join(metrics)}")
        
        # Add metadata if available
        if pattern.metadata:
            metadata_str = ", ".join([f"{k}: {v}" for k, v in pattern.metadata.items()])
            context_parts.append(f"Additional info: {metadata_str}")
        
        return " | ".join(context_parts)
    
    def add_pattern(self, pattern: ConsumptionPattern) -> bool:
        """Add a consumption pattern to the vector store"""
        try:
            # Create contextual description
            context_text = self._create_pattern_context(pattern)
            
            # Generate embedding
            embedding = self._generate_embedding(context_text)
            
            # Add to ChromaDB
            self.collection.add(
                ids=[pattern.pattern_id],
                embeddings=[embedding],
                documents=[context_text],
                metadatas=[{
                    "node_id": pattern.node_id,
                    "timestamp": pattern.timestamp,
                    "context": pattern.context,
                    "consumption_data": json.dumps(pattern.consumption_data),
                    "metadata": json.dumps(pattern.metadata)
                }]
            )
            
            logger.debug(f"Added pattern {pattern.pattern_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add pattern {pattern.pattern_id}: {e}")
            return False
    
    def add_patterns_batch(self, patterns: List[ConsumptionPattern]) -> int:
        """Add multiple patterns to the vector store in batch"""
        try:
            if not patterns:
                return 0
            
            # Prepare batch data
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for pattern in patterns:
                context_text = self._create_pattern_context(pattern)
                embedding = self._generate_embedding(context_text)
                
                ids.append(pattern.pattern_id)
                embeddings.append(embedding)
                documents.append(context_text)
                metadatas.append({
                    "node_id": pattern.node_id,
                    "timestamp": pattern.timestamp,
                    "context": pattern.context,
                    "consumption_data": json.dumps(pattern.consumption_data),
                    "metadata": json.dumps(pattern.metadata)
                })
            
            # Add batch to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(patterns)} patterns to vector store")
            return len(patterns)
            
        except Exception as e:
            logger.error(f"Failed to add patterns batch: {e}")
            return 0
    
    def search_similar_patterns(self, 
                              query_context: str, 
                              k: int = 5,
                              node_filter: Optional[List[str]] = None) -> List[SimilarPattern]:
        """Search for similar consumption patterns"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query_context)
            
            # Prepare where clause for filtering
            where_clause = None
            if node_filter:
                where_clause = {"node_id": {"$in": node_filter}}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause
            )
            
            # Parse results
            similar_patterns = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    pattern_id = results['ids'][0][i]
                    distance = results['distances'][0][i]
                    similarity_score = 1.0 - distance  # Convert distance to similarity
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    
                    # Parse metadata
                    consumption_data = json.loads(metadata.get('consumption_data', '{}'))
                    pattern_metadata = json.loads(metadata.get('metadata', '{}'))
                    
                    similar_patterns.append(SimilarPattern(
                        pattern_id=pattern_id,
                        similarity_score=similarity_score,
                        context=metadata.get('context', ''),
                        consumption_data=consumption_data,
                        metadata=pattern_metadata
                    ))
            
            logger.debug(f"Found {len(similar_patterns)} similar patterns")
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Failed to search similar patterns: {e}")
            return []
    
    def generate_prediction(self, request: PredictionRequest) -> PredictionResponse:
        """Generate demand prediction using RAG approach with Pathway LLM optimization"""
        try:
            start_time = time.time()
            
            # Use Pathway LLM if available for enhanced performance
            if self.pathway_system:
                try:
                    response = self.pathway_system.generate_prediction_pathway(request)
                    processing_time = time.time() - start_time
                    logger.info(f"Generated Pathway prediction in {processing_time:.3f}s")
                    return response
                except Exception as e:
                    logger.warning(f"Pathway LLM failed, falling back to standard RAG: {e}")
            
            # Fallback to standard RAG implementation
            return self._generate_standard_prediction(request, start_time)
            
        except Exception as e:
            logger.error(f"Failed to generate prediction: {e}")
            # Return fallback response
            return PredictionResponse(
                prediction="Unable to generate prediction due to system error. Please check system status.",
                similar_patterns=[],
                confidence_score=0.0,
                optimization_recommendations=["Check system connectivity", "Verify data availability"],
                timestamp=time.time()
            )
    
    def _generate_standard_prediction(self, request: PredictionRequest, start_time: float) -> PredictionResponse:
        """Generate prediction using standard RAG approach (fallback method)"""
        # Search for similar patterns
        similar_patterns = self.search_similar_patterns(
            query_context=request.current_context,
            k=5,
            node_filter=request.node_ids
        )
        
        # Generate prediction using LLM if we have similar patterns
        if similar_patterns:
            prediction_text = self._generate_llm_prediction(
                current_context=request.current_context,
                similar_patterns=similar_patterns,
                time_horizon=request.time_horizon
            )
            confidence_score = min(0.9, sum(p.similarity_score for p in similar_patterns) / len(similar_patterns))
        else:
            prediction_text = "Insufficient historical data for accurate prediction. Consider baseline demand patterns."
            confidence_score = 0.1
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(similar_patterns)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"Generated standard prediction in {processing_time:.3f}s")
        
        return PredictionResponse(
            prediction=prediction_text,
            similar_patterns=similar_patterns,
            confidence_score=confidence_score,
            optimization_recommendations=recommendations,
            timestamp=time.time()
        )
    
    def _generate_llm_prediction(self, 
                               current_context: str,
                               similar_patterns: List[SimilarPattern],
                               time_horizon: int) -> str:
        """Generate prediction using OpenAI LLM or fallback"""
        try:
            if self.use_mock_embeddings or not self.openai_client:
                # Generate mock prediction for development
                return f"""Based on {len(similar_patterns)} similar historical patterns, predicted energy demand for the next {time_horizon} hour(s):

Predicted Demand: {150 + len(similar_patterns) * 25}kW (estimated)

Key Factors:
- Historical pattern similarity indicates moderate to high demand
- Current context suggests increased operational requirements
- {time_horizon}-hour forecast shows stable consumption trend

Confidence: Moderate (based on {len(similar_patterns)} similar patterns)

Risks to Monitor:
- Potential demand spikes during peak hours
- Equipment availability and grid stability
- Emergency scenarios requiring additional capacity

Note: This is a development prediction. Set OPENAI_API_KEY for full AI-powered forecasting."""
            
            # Prepare context from similar patterns
            patterns_context = []
            for i, pattern in enumerate(similar_patterns[:3], 1):  # Use top 3 patterns
                patterns_context.append(
                    f"Pattern {i} (similarity: {pattern.similarity_score:.2f}):\n"
                    f"Context: {pattern.context}\n"
                    f"Consumption: {pattern.consumption_data}\n"
                )
            
            # Create prompt
            prompt = f"""
Based on the following historical energy consumption patterns, predict the energy demand for the next {time_horizon} hour(s).

Current Context: {current_context}

Historical Patterns:
{chr(10).join(patterns_context)}

Please provide:
1. Predicted energy demand in kW
2. Key factors influencing the prediction
3. Confidence level and reasoning
4. Potential risks or anomalies to watch for

Keep the response concise and actionable for grid operators.
"""
            
            # Call OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert energy grid analyst providing demand forecasts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate LLM prediction: {e}")
            return f"Based on {len(similar_patterns)} similar patterns, expect moderate demand fluctuation. Monitor closely for {time_horizon}h horizon."
    
    def _generate_optimization_recommendations(self, similar_patterns: List[SimilarPattern]) -> List[str]:
        """Generate optimization recommendations based on patterns"""
        recommendations = []
        
        if not similar_patterns:
            recommendations.extend([
                "Collect more historical data for better predictions",
                "Monitor current consumption trends closely",
                "Maintain conservative power allocation"
            ])
            return recommendations
        
        # Analyze patterns for recommendations
        avg_similarity = sum(p.similarity_score for p in similar_patterns) / len(similar_patterns)
        
        if avg_similarity > 0.8:
            recommendations.append("High pattern similarity detected - predictions are reliable")
        elif avg_similarity > 0.6:
            recommendations.append("Moderate pattern similarity - monitor for deviations")
        else:
            recommendations.append("Low pattern similarity - use conservative estimates")
        
        # Add general recommendations
        recommendations.extend([
            "Prioritize renewable sources during peak demand",
            "Prepare backup diesel generators for critical nodes",
            "Monitor tier 1 (hospital) nodes continuously"
        ])
        
        return recommendations
    
    def get_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            count = self.collection.count()
            stats = {
                "total_patterns": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model,
                "embedding_dimension": self.embedding_dimension,
                "store_path": self.vector_store_path,
                "pathway_llm_enabled": self.pathway_system is not None
            }
            
            # Add Pathway performance stats if available
            if self.pathway_system:
                pathway_stats = self.pathway_system.get_performance_stats()
                stats["pathway_performance"] = pathway_stats
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get store stats: {e}")
            return {"error": str(e)}
    
    def optimize_for_performance(self):
        """Optimize system for 2-second response time target"""
        try:
            if self.pathway_system:
                self.pathway_system.optimize_for_performance()
                logger.info("Applied Pathway LLM performance optimizations")
            else:
                logger.info("Pathway LLM not available - using standard optimizations")
                # Apply standard optimizations here if needed
                
        except Exception as e:
            logger.error(f"Failed to optimize performance: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {
            "system_type": "hybrid" if self.pathway_system else "standard",
            "embedding_model": self.embedding_model,
            "vector_store_size": self.collection.count() if hasattr(self, 'collection') else 0
        }
        
        if self.pathway_system:
            pathway_metrics = self.pathway_system.get_performance_stats()
            metrics.update(pathway_metrics)
        
        return metrics
    
    def clear_store(self) -> bool:
        """Clear all patterns from the vector store"""
        try:
            # Delete and recreate collection
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear store: {e}")
            return False

# Utility functions for data loading and pattern creation

def load_historical_data_from_csv(csv_path: str) -> List[ConsumptionPattern]:
    """Load historical consumption patterns from CSV file"""
    try:
        df = pd.read_csv(csv_path)
        patterns = []
        
        for _, row in df.iterrows():
            pattern = ConsumptionPattern(
                pattern_id=f"pattern_{row.get('node_id', 'unknown')}_{int(row.get('timestamp', time.time()))}",
                timestamp=row.get('timestamp', time.time()),
                node_id=row.get('node_id', 'unknown'),
                consumption_data={
                    'current_load': float(row.get('current_load', 0)),
                    'peak_load': float(row.get('peak_load', row.get('current_load', 0))),
                    'avg_load': float(row.get('avg_load', row.get('current_load', 0)))
                },
                context=f"Historical pattern for {row.get('source_type', 'unknown')} node at {row.get('status', 'unknown')} status",
                metadata={
                    'priority_tier': row.get('priority_tier', 3),
                    'source_type': row.get('source_type', 'Grid'),
                    'status': row.get('status', 'active'),
                    'location': {
                        'lat': row.get('lat', 0.0),
                        'lng': row.get('lng', 0.0)
                    }
                }
            )
            patterns.append(pattern)
        
        logger.info(f"Loaded {len(patterns)} patterns from {csv_path}")
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to load historical data from {csv_path}: {e}")
        return []

def create_sample_patterns() -> List[ConsumptionPattern]:
    """Create sample consumption patterns for testing"""
    patterns = []
    base_time = time.time() - (7 * 24 * 3600)  # 7 days ago
    
    # Sample patterns for different scenarios
    scenarios = [
        {
            "node_id": "hospital_001",
            "context": "Hospital during normal operations",
            "consumption": {"current_load": 150.0, "peak_load": 200.0, "avg_load": 140.0},
            "metadata": {"priority_tier": 1, "source_type": "Grid", "status": "active"}
        },
        {
            "node_id": "hospital_001", 
            "context": "Hospital during emergency surge",
            "consumption": {"current_load": 220.0, "peak_load": 250.0, "avg_load": 200.0},
            "metadata": {"priority_tier": 1, "source_type": "Grid", "status": "active"}
        },
        {
            "node_id": "factory_001",
            "context": "Factory during peak production hours",
            "consumption": {"current_load": 300.0, "peak_load": 350.0, "avg_load": 280.0},
            "metadata": {"priority_tier": 2, "source_type": "Grid", "status": "active"}
        },
        {
            "node_id": "factory_001",
            "context": "Factory during maintenance shutdown",
            "consumption": {"current_load": 50.0, "peak_load": 80.0, "avg_load": 45.0},
            "metadata": {"priority_tier": 2, "source_type": "Grid", "status": "degraded"}
        },
        {
            "node_id": "residential_001",
            "context": "Residential area during evening peak",
            "consumption": {"current_load": 80.0, "peak_load": 100.0, "avg_load": 75.0},
            "metadata": {"priority_tier": 3, "source_type": "Grid", "status": "active"}
        }
    ]
    
    for i, scenario in enumerate(scenarios):
        pattern = ConsumptionPattern(
            pattern_id=f"sample_pattern_{i+1}",
            timestamp=base_time + (i * 3600),  # 1 hour apart
            node_id=scenario["node_id"],
            consumption_data=scenario["consumption"],
            context=scenario["context"],
            metadata=scenario["metadata"]
        )
        patterns.append(pattern)
    
    return patterns

# Example usage and testing
if __name__ == "__main__":
    # Initialize RAG system
    rag = EnergyRAG()
    
    # Create and add sample patterns
    sample_patterns = create_sample_patterns()
    rag.add_patterns_batch(sample_patterns)
    
    # Test prediction
    request = PredictionRequest(
        current_context="Hospital experiencing increased patient load during evening hours",
        node_ids=["hospital_001"],
        time_horizon=2
    )
    
    response = rag.generate_prediction(request)
    print(f"Prediction: {response.prediction}")
    print(f"Confidence: {response.confidence_score:.2f}")
    print(f"Similar patterns found: {len(response.similar_patterns)}")
    
    # Print store stats
    stats = rag.get_store_stats()
    print(f"Store stats: {stats}")