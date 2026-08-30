import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import DB_PATH

class TestDatabase:
    def test_db_path_exists(self):
        assert DB_PATH is not None
        assert "compliance.db" in DB_PATH
