import asyncpg
from typing import Dict, List, Any, Optional
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Dict 기반 데이터베이스 관리자"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """연결 풀 생성"""
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created")
    
    async def disconnect(self):
        """연결 풀 종료"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """연결 획득 컨텍스트 매니저"""
        async with self._pool.acquire() as connection:
            yield connection
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """모든 행을 Dict 리스트로 반환"""
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """단일 행을 Dict로 반환"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_value(self, query: str, *args) -> Any:
        """단일 값 반환"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args) -> str:
        """쿼리 실행"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]):
        """여러 쿼리 실행"""
        async with self.acquire() as conn:
            await conn.executemany(query, args_list)
    
    async def execute_batch(self, queries: List[tuple]):
        """트랜잭션으로 여러 쿼리 실행"""
        async with self.acquire() as conn:
            async with conn.transaction():
                for query, *args in queries:
                    await conn.execute(query, *args)