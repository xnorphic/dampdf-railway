# File: app/services/session_manager.py

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)

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
                
                # Clean up expired sessions from memory
                self._cleanup_expired_sessions()
                
            logger.debug("Session data stored", session_id=session_id, expire_hours=expire_hours)
        except Exception as e:
            logger.error("Failed to store session data", error=str(e), session_id=session_id)
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
                elif session_data:
                    # Clean up expired session
                    del self._in_memory_store[session_id]
            return None
        except Exception as e:
            logger.error("Failed to get session data", error=str(e), session_id=session_id)
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        try:
            if self.redis_pool:
                result = await self.redis_pool.delete(f"session:{session_id}")
                return result > 0
            else:
                if session_id in self._in_memory_store:
                    del self._in_memory_store[session_id]
                    return True
            return False
        except Exception as e:
            logger.error("Failed to delete session", error=str(e), session_id=session_id)
            return False
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions from in-memory store"""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session_data in self._in_memory_store.items()
            if session_data["expires_at"] < now
        ]
        
        for session_id in expired_sessions:
            del self._in_memory_store[session_id]
        
        if expired_sessions:
            logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def track_usage(self, session_id: str, user_id: str = None, tool_type: str = None, file_size: int = None):
        """Track usage for analytics and billing purposes"""
        try:
            usage_data = {
                "timestamp": datetime.now(),
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "tool_type": tool_type,
                "file_size": file_size,
                "ip_address": None,  # You'd get this from the request
                "user_agent": None   # You'd get this from the request
            }
            
            if self.redis_pool:
                # Add to a Redis list for later processing
                await self.redis_pool.lpush("usage_tracking", json.dumps(usage_data, default=str))
                # Keep list at a reasonable size
                await self.redis_pool.ltrim("usage_tracking", 0, 9999)
            else:
                # In memory tracking (limited)
                if not hasattr(self, "_usage_tracking"):
                    self._usage_tracking = []
                self._usage_tracking.append(usage_data)
                # Keep list at a reasonable size
                if len(self._usage_tracking) > 1000:
                    self._usage_tracking = self._usage_tracking[-1000:]
                    
            logger.debug("Usage tracked", session_id=session_id, tool_type=tool_type)
        except Exception as e:
            logger.error("Failed to track usage", error=str(e), session_id=session_id)
            # Don't raise - tracking failure shouldn't break the main flow

# Global session manager
session_manager = SessionManager()
