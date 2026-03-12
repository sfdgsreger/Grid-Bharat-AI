# Core data models for Bharat-Grid AI
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Location(BaseModel):
    """Geographic location coordinates"""
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")

class EnergyNode(BaseModel):
    """Energy consumption node with priority-based allocation"""
    node_id: str = Field(..., description="Unique identifier for the energy node")
    current_load: float = Field(..., ge=0, description="Current power demand in kW")
    priority_tier: Literal[1, 2, 3] = Field(..., description="Priority tier: 1=Hospital, 2=Factory, 3=Residential")
    source_type: Literal['Grid', 'Solar', 'Battery', 'Diesel'] = Field(..., description="Primary power source type")
    status: Literal['active', 'inactive', 'degraded'] = Field(..., description="Current operational status")
    location: Location = Field(..., description="Geographic coordinates")
    timestamp: float = Field(..., description="Unix timestamp of the data point")

class AvailableSources(BaseModel):
    """Available power from different sources"""
    grid: float = Field(default=0, ge=0, description="Available grid power in kW")
    solar: float = Field(default=0, ge=0, description="Available solar power in kW")
    battery: float = Field(default=0, ge=0, description="Available battery power in kW")
    diesel: float = Field(default=0, ge=0, description="Available diesel power in kW")

class SupplyEvent(BaseModel):
    """Power supply change event"""
    event_id: str = Field(..., description="Unique identifier for the supply event")
    total_supply: float = Field(..., ge=0, description="Total available power supply in kW")
    available_sources: AvailableSources = Field(..., description="Breakdown of power by source")
    timestamp: float = Field(..., description="Unix timestamp of the supply event")

class SourceMix(BaseModel):
    """Power allocation breakdown by source"""
    grid: Optional[float] = Field(default=None, ge=0, description="Allocated grid power in kW")
    solar: Optional[float] = Field(default=None, ge=0, description="Allocated solar power in kW")
    battery: Optional[float] = Field(default=None, ge=0, description="Allocated battery power in kW")
    diesel: Optional[float] = Field(default=None, ge=0, description="Allocated diesel power in kW")

class AllocationResult(BaseModel):
    """Power allocation decision for a specific node"""
    node_id: str = Field(..., description="Target energy node identifier")
    allocated_power: float = Field(..., ge=0, description="Total allocated power in kW")
    source_mix: SourceMix = Field(..., description="Power allocation breakdown by source")
    action: Literal['maintain', 'reduce', 'cutoff'] = Field(..., description="Allocation action taken")
    latency_ms: float = Field(..., ge=0, description="Processing latency in milliseconds")

# Additional utility models for API responses
class GridFailureRequest(BaseModel):
    """Request model for grid failure simulation"""
    failure_percentage: float = Field(..., ge=0, le=1, description="Percentage of supply to reduce (0.0-1.0)")

class GridFailureResponse(BaseModel):
    """Response model for grid failure simulation"""
    status: str = Field(..., description="Simulation status")
    reduction: float = Field(..., description="Applied reduction percentage")

class InsightsResponse(BaseModel):
    """Response model for AI insights"""
    insights: str = Field(..., description="AI-generated demand predictions and recommendations")
    timestamp: float = Field(..., description="Timestamp of the prediction")

class LatencyMetric(BaseModel):
    """WebSocket latency metric"""
    type: Literal['latency'] = Field(default='latency', description="Message type identifier")
    value: float = Field(..., ge=0, description="Latency value in milliseconds")