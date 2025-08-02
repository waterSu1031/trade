import pytest
from trade_common.db import DatabaseManager


@pytest.mark.asyncio
async def test_database_manager_initialization():
    """DatabaseManager 초기화 테스트"""
    db = DatabaseManager("postgresql://test:test@localhost/test")
    assert db._pool is None
    assert db._dsn == "postgresql://test:test@localhost/test"