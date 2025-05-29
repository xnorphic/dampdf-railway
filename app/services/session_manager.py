import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class SessionManager:
    def __init__(self):
        self.redis_pool = None
        self._in_memory_store = {}
    
    async def connect(self):
        try:
            import aioredis
            from app.core.config import settings
            self.redis_pool = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await self.redis_pool.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning("Redis connection failed, using in-memory storage", error=str(e))
            self.redis_pool = None
    
    def generate_session_id(self) -> str:
        return str(uuid.uuid4())
    
    async def store_session_data(self, session_id: str, data: Dict[str, Any], expire_hours: int = 24):
        try:
            if self.redis_pool:
                await self.redis_pool.setex(
                    f"session:{session_id}",
                    timedelta(hours=expire_hours),
                    json.dumps(data, default=str)
                )
            else:
                self._in_memory_store[session_id] = {
                    "data": data,
                    "expires_at": datetime.now() + timedelta(hours=expire_hours)
                }
        except Exception as e:
            logger.error("Failed to store session data", error=str(e))
            raise
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            if self.redis_pool:
                data = await self.redis_pool.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
            else:
                session_data = self._in_memory_store.get(session_id)
                if session_data and session_data["expires_at"] > datetime.now():
                    return session_data["data"]
            return None
        except Exception as e:
            logger.error("Failed to get session data", error=str(e))
            return None

# Global session manager
session_manager = SessionManager()
