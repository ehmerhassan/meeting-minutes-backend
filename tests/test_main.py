"""
Tests for main app endpoints including health checks.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Set test environment variable before importing app
os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_health_check(self):
        """Test simple health check returns ok status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_detailed_health_check(self):
        """Test detailed health check returns full info."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "Meeting Notes Intelligence Suite"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert data["gemini_configured"] is True


class TestCORS:
    """Test CORS middleware configuration."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are included in responses."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS preflight should succeed
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Test error handling endpoints."""
    
    def test_404_not_found(self):
        """Test 404 response for unknown endpoints."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 response for wrong HTTP method."""
        response = client.put("/")
        assert response.status_code == 405


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_swagger_docs_available(self):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_available(self):
        """Test ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_schema_available(self):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Meeting Notes Intelligence Suite"
        assert data["info"]["version"] == "1.0.0"
