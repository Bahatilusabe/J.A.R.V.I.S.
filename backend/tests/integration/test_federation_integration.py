"""
Federation Page - Frontend-Backend Integration Tests
Tests all federation endpoints used by the Frontend Federation.tsx page
Ensures complete end-to-end data flow for:
- Network view (node listing, sync triggering)
- Models view (model provenance)
- Analytics view (statistics and trends)
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestFederationNodeEndpoints:
    """Test federation node endpoints used by network view"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_get_federation_nodes(self, client):
        """Test GET /api/federation/nodes - fetches all nodes for network view"""
        response = client.get("/api/federation/nodes")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches frontend expectations
        assert "nodes" in data
        assert "total" in data
        assert "active" in data
        assert "network_health" in data
        assert "network_trust" in data
        assert "timestamp" in data
        
        # Verify nodes structure
        nodes = data["nodes"]
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        
        # Verify each node has required fields for frontend
        for node in nodes:
            assert "id" in node
            assert "country" in node
            assert "tag" in node
            assert "sync_health" in node
            assert "trust_score" in node
            assert "last_ledger" in node
            assert "last_sync" in node
            assert "active" in node
            
            # Verify field types and ranges
            assert isinstance(node["id"], str)
            assert isinstance(node["country"], str)
            assert isinstance(node["tag"], str)
            assert 0.0 <= node["sync_health"] <= 1.0
            assert 0.0 <= node["trust_score"] <= 1.0
            assert isinstance(node["last_ledger"], str)
            assert isinstance(node["last_sync"], str)
            assert isinstance(node["active"], bool)

    def test_federation_nodes_demo_data(self, client):
        """Test that demo nodes include expected nodes"""
        response = client.get("/api/federation/nodes")
        data = response.json()
        nodes = data["nodes"]
        
        # Verify demo nodes exist
        node_ids = [n["id"] for n in nodes]
        assert "node-us-1" in node_ids
        assert "node-eu-1" in node_ids
        assert "node-asia-1" in node_ids

    def test_trigger_node_sync(self, client):
        """Test POST /api/federation/nodes/{node_id}/sync - triggers sync for network view"""
        # First get existing nodes
        nodes_response = client.get("/api/federation/nodes")
        nodes = nodes_response.json()["nodes"]
        test_node_id = nodes[0]["id"]
        
        # Trigger sync
        sync_response = client.post(f"/api/federation/nodes/{test_node_id}/sync")
        assert sync_response.status_code == 200
        
        data = sync_response.json()
        assert "status" in data
        assert "message" in data
        assert "node_id" in data
        assert "triggered_at" in data
        
        assert data["status"] == "success"
        assert data["node_id"] == test_node_id

    def test_trigger_sync_nonexistent_node(self, client):
        """Test sync on nonexistent node returns 404"""
        response = client.post("/api/federation/nodes/nonexistent/sync")
        assert response.status_code == 404


class TestFederationModelEndpoints:
    """Test federation model endpoints used by models view"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_get_federation_models(self, client):
        """Test GET /api/federation/models - fetches all models for models view"""
        response = client.get("/api/federation/models")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches frontend expectations
        assert "models" in data
        assert "total" in data
        assert "timestamp" in data
        
        # Verify models structure
        models = data["models"]
        assert isinstance(models, list)
        assert len(models) >= 0
        
        # Verify each model has required fields for frontend
        for model in models:
            assert "id" in model
            assert "version" in model
            assert "node_id" in model
            assert "created_at" in model
            assert "status" in model
            
            # Verify field types
            assert isinstance(model["id"], str)
            assert isinstance(model["version"], str)
            assert isinstance(model["node_id"], str)
            assert isinstance(model["created_at"], str)
            assert model["status"] in ["training", "aggregated", "validated"]

    def test_federation_models_demo_data(self, client):
        """Test that demo models exist"""
        response = client.get("/api/federation/models")
        data = response.json()
        models = data["models"]
        
        # Verify demo models exist
        model_ids = [m["id"] for m in models]
        assert "model-v1" in model_ids
        assert "model-v2" in model_ids
        assert "model-v3" in model_ids


class TestFederationStatisticsEndpoints:
    """Test federation statistics endpoints used by analytics view"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_get_federation_stats(self, client):
        """Test GET /api/federation/stats - fetches network statistics for analytics view"""
        response = client.get("/api/federation/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches frontend expectations
        assert "total_nodes" in data
        assert "active_nodes" in data
        assert "network_health" in data
        assert "network_trust" in data
        assert "total_models" in data
        assert "aggregation_status" in data
        assert "privacy_level" in data
        assert "sync_efficiency" in data
        assert "timestamp" in data
        
        # Verify field types and ranges
        assert isinstance(data["total_nodes"], int)
        assert isinstance(data["active_nodes"], int)
        assert 0.0 <= data["network_health"] <= 1.0
        assert 0.0 <= data["network_trust"] <= 1.0
        assert isinstance(data["total_models"], int)
        assert isinstance(data["aggregation_status"], str)
        assert 0 <= data["privacy_level"] <= 100
        assert 0 <= data["sync_efficiency"] <= 100

    def test_aggregation_status(self, client):
        """Test GET /api/federation/aggregation-status"""
        response = client.get("/api/federation/aggregation-status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "progress" in data
        assert "aggregation_id" in data
        assert "timestamp" in data
        
        # Verify field values
        assert data["status"] in ["idle", "in-progress", "completed"]
        assert 0 <= data["progress"] <= 100


class TestFederationHistoryEndpoints:
    """Test federation history endpoints used by node detail panel"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_get_node_history(self, client):
        """Test GET /api/federation/nodes/{node_id}/history - fetches history for detail panel"""
        # First get existing nodes
        nodes_response = client.get("/api/federation/nodes")
        nodes = nodes_response.json()["nodes"]
        test_node_id = nodes[0]["id"]
        
        # Fetch history
        response = client.get(f"/api/federation/nodes/{test_node_id}/history?limit=24")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches frontend expectations
        assert "node_id" in data
        assert "history" in data
        assert "stats" in data
        assert "timestamp" in data
        
        assert data["node_id"] == test_node_id
        
        # Verify history structure
        history = data["history"]
        assert isinstance(history, list)
        
        # If history exists, verify each entry
        for entry in history:
            assert "timestamp" in entry
            assert "node_id" in entry
            assert "sync_health" in entry
            assert "trust_score" in entry
            assert "last_ledger" in entry
            assert "active" in entry
            
            # Verify ranges
            assert 0.0 <= entry["sync_health"] <= 1.0
            assert 0.0 <= entry["trust_score"] <= 1.0

    def test_node_history_limit_parameter(self, client):
        """Test limit parameter for history endpoint"""
        nodes_response = client.get("/api/federation/nodes")
        nodes = nodes_response.json()["nodes"]
        test_node_id = nodes[0]["id"]
        
        # Test with different limits
        response = client.get(f"/api/federation/nodes/{test_node_id}/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 10 entries
        assert len(data["history"]) <= 10

    def test_node_history_nonexistent_node(self, client):
        """Test history for nonexistent node returns 404"""
        response = client.get("/api/federation/nodes/nonexistent/history")
        assert response.status_code == 404


class TestFederationAggregationEndpoint:
    """Test federation aggregation endpoint used by aggregation button"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_trigger_aggregation(self, client):
        """Test POST /api/federation/aggregate - triggers global aggregation"""
        response = client.post("/api/federation/aggregate")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "message" in data
        assert "aggregation_id" in data
        assert "progress" in data
        assert "started_at" in data
        
        # Verify values
        assert data["status"] == "success"
        assert data["progress"] == 100


class TestFederationDataFlow:
    """Test complete data flow through Federation page"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_complete_federation_workflow(self, client):
        """
        Test complete workflow:
        1. Load all federation data (nodes, models, stats)
        2. Select a node and fetch its history
        3. Trigger sync on selected node
        4. Trigger global aggregation
        5. Verify data refreshes
        """
        # Step 1: Load initial federation data
        nodes_resp = client.get("/api/federation/nodes")
        models_resp = client.get("/api/federation/models")
        stats_resp = client.get("/api/federation/stats")
        
        assert nodes_resp.status_code == 200
        assert models_resp.status_code == 200
        assert stats_resp.status_code == 200
        
        nodes_data = nodes_resp.json()
        models_data = models_resp.json()
        stats_data = stats_resp.json()
        
        # Step 2: Select first node and fetch history
        first_node = nodes_data["nodes"][0]
        history_resp = client.get(f"/api/federation/nodes/{first_node['id']}/history?limit=24")
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        
        # Step 3: Trigger sync
        sync_resp = client.post(f"/api/federation/nodes/{first_node['id']}/sync")
        assert sync_resp.status_code == 200
        
        # Step 4: Trigger aggregation
        agg_resp = client.post("/api/federation/aggregate")
        assert agg_resp.status_code == 200
        
        # Step 5: Verify stats endpoint (used for refresh)
        refresh_stats_resp = client.get("/api/federation/stats")
        assert refresh_stats_resp.status_code == 200


class TestFederationErrorHandling:
    """Test error handling for fallback to demo data"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.api.server import app
        return TestClient(app)

    def test_invalid_limit_parameter(self, client):
        """Test invalid limit parameter"""
        nodes_response = client.get("/api/federation/nodes")
        nodes = nodes_response.json()["nodes"]
        test_node_id = nodes[0]["id"]
        
        # Test with limit > 100 (should be rejected)
        response = client.get(f"/api/federation/nodes/{test_node_id}/history?limit=101")
        assert response.status_code == 422  # Validation error

    def test_invalid_limit_negative(self, client):
        """Test negative limit parameter"""
        nodes_response = client.get("/api/federation/nodes")
        nodes = nodes_response.json()["nodes"]
        test_node_id = nodes[0]["id"]
        
        # Test with negative limit
        response = client.get(f"/api/federation/nodes/{test_node_id}/history?limit=-1")
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
