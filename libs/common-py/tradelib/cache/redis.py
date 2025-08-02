import redis.asyncio as redis
from typing import Any, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 캐시 관리자"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Redis 연결"""
        if not self._client:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            logger.info("Connected to Redis")
    
    async def disconnect(self):
        """연결 해제"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        value = await self._client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, expire: int = None):
        """값 저장"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        if expire:
            await self._client.setex(key, expire, value)
        else:
            await self._client.set(key, value)
    
    async def delete(self, key: str):
        """키 삭제"""
        await self._client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        return await self._client.exists(key) > 0
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """해시 값 조회"""
        value = await self._client.hget(name, key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def hset(self, name: str, key: str, value: Any):
        """해시 값 저장"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self._client.hset(name, key, value)
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """해시 전체 조회"""
        data = await self._client.hgetall(name)
        result = {}
        for key, value in data.items():
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                result[key] = value
        return result