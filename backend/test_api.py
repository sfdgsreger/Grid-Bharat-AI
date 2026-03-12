"""
Tests for the FastAPI application.

This module tests the basic functionality of the API endpoints,
CORS configuration, and error handling.
"""

import pytest
from fastapi.testclient import TestClient

from api import app

# Create test client
client = TestClient(app)


class TestBasicEndpoints:
    """Test basic API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Bharat-Grid AI API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "timestamp" in data
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestGridFailureSimulation:
    """Test grid failure simulation endpoint."""
    
    def test_valid_grid_failure(self):
        """Test valid grid failure simulation."""
        request_data = {"failure_percentage": 0.3}
        
        response = client.post("/simulate/grid-failure", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "simulated"
        assert data["reduction"] == 0.3
        assert "timestamp" in data
    
    def test_invalid_failure_percentage_high(self):
        """Test invalid failure percentage (too high)."""
        request_data = {"failure_percentage": 1.5}
        
        response = client.post("/simulate/grid-failure", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_failure_percentage_negative(self):
        """Test invalid failure percentage (negative)."""
        request_data = {"failure_percentage": -0.1}
        
        response = client.post("/simulate/grid-failure", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_failure_percentage(self):
        """Test missing failure percentage."""
        response = client.post("/simulate/grid-failure", json={})
        
        assert response.status_code == 422  # Validation error


class TestInsightsEndpoint:
    """Test AI insights endpoint."""
    
    def test_get_insights(self):
        """Test getting AI insights."""
        response = client.get("/insights")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "insights" in data
        assert "timestamp" in data
        assert "response_time_ms" in data
        assert isinstance(data["response_time_ms"], float)
        assert data["response_time_ms"] >= 0


class TestErrorHandling:
    """Test error handling and logging."""
    
    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])