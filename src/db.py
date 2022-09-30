from redis import asyncio as aioredis

redis_instance = aioredis.Redis(
    host='localhost',
    port=6379,
    db=0,
)

if __name__ == '__main__':
    pass
