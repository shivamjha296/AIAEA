import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

client = TestClient(app)

class TestAPI:
    def test_app_exists(self):
        assert app is not None
        assert app.title == "Regulatory Compliance Radar API"
