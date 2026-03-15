from redis.asyncio import ConnectionPool, Redis
from uuid import UUID
import json
class RedisService():
    def __init__(self, redis_url : str):

        self.pool = ConnectionPool.from_url(f"{redis_url}", decode_responses = True)
        self._client= Redis(connection_pool=self.pool)
    async def close(self):
        await  self._client.close()
    async def add_to_blacklist(self, jti: str, ttl : int):
        key = f"jwt_blacklist:{jti}"
        await self._client.setex(key, ttl, "1")
    async def is_in_blacklist(self, jti : str):
        result = await self._client.exists(f"jwt_blacklist:{jti}")
        return bool(result)
    def _gen_chat_key(self, user_id : UUID, chat_id : UUID)->str:
        return f"chat:history:{user_id}:{chat_id}"
    async def push_messages(self, user_id: UUID, chat_id: UUID, messages : list[dict]):
        key= self._gen_chat_key(user_id, chat_id)
        payloads = [json.dumps(m) for m in messages]
        async with self._client.pipeline(transaction=True) as pipe:
            await pipe.rpush(key, *payloads)
            await pipe.ltrim(key, -10, -1)
            await pipe.expire(key, 3600)
            await pipe.execute()
    async def get_history(self,user_id : UUID,  chat_id: UUID ) -> list[dict]:
        key = self._gen_chat_key(user_id, chat_id)
        raw_history = await self._client.lrange(key, 0, -1)
        return [json.loads(msg) for msg in raw_history]
    async def delete_history(self, user_id: UUID, chat_id: UUID):
        key = self._gen_chat_key(user_id, chat_id)
        await self._client.delete(key)
    async def check_chat_access(self, user_id: UUID, chat_id: UUID) -> bool | None:
        """Перевіряє в кеші, чи має юзер доступ до чату. Повертає None, якщо кеш порожній."""
        key = f"access:{user_id}:{chat_id}"
        val = await self._client.get(key)
        if val is None:
            return None
        return val == "true" # Якщо в Редісі є "true", значить доступ є

    async def grant_chat_access(self, user_id: UUID, chat_id: UUID, ttl_seconds: int = 3600):
        """Видає 'перепустку' в Редіс на 1 годину (3600 секунд)"""
        key = f"access:{user_id}:{chat_id}"
        await self._client.setex(key, ttl_seconds, "true")