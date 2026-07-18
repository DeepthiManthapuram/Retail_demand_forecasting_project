"""
tests/test_api.py
=================
Integration tests for the FastAPI endpoints using TestClient.
"""

import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from backend.main import app

client = TestClient(app)


class TestHealthEndpoints:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data


class TestDatasetEndpoint:
    def test_dataset_info(self):
        resp = client.get("/api/dataset-info")
        assert resp.status_code == 200


class TestModelInfoEndpoint:
    def test_model_info(self):
        resp = client.get("/api/model-info")
        assert resp.status_code == 200
        data = resp.json()
        assert "saved_models" in data
        assert "available_types" in data


class TestPredictValidation:
    def test_invalid_store(self):
        resp = client.post("/api/predict", json={"store": 99, "item": 1, "horizon": 30, "model": "auto"})
        assert resp.status_code in (422, 404)

    def test_invalid_horizon(self):
        resp = client.post("/api/predict", json={"store": 1, "item": 1, "horizon": 999, "model": "auto"})
        assert resp.status_code == 422

    def test_invalid_item(self):
        resp = client.post("/api/predict", json={"store": 1, "item": 999, "horizon": 30, "model": "auto"})
        assert resp.status_code in (422, 404)


class TestDashboardEndpoint:
    def test_dashboard(self):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "kpi" in data


class TestAuthEndpoints:
    _TEST_USER = {"username": "testuser_api", "email": "testapi@example.com", "password": "test1234"}

    def test_register(self):
        resp = client.post("/auth/register", json=self._TEST_USER)
        # 200 = success, 400 = already exists (both are valid in repeated test runs)
        assert resp.status_code in (200, 400)

    def test_login_wrong_password(self):
        from urllib.parse import urlencode
        body = urlencode({"username": "nonexistent", "password": "wrongpass"})
        resp = client.post(
            "/auth/login",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    def test_me_without_token(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
