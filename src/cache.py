import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Any
from config import Settings

OnAction = Callable[..., Awaitable[Any]]
logging.basicConfig(format=Settings.log.format)
logging.root.setLevel(Settings.log.level)


class CacheBase(ABC):
    def __init__(self, expire_time=3600):
        self._lock = asyncio.Lock()
        self._expire_time = expire_time
        self._cache = None
        self._last_cache_timestamp = None

    async def reset(self):
        self._last_cache_timestamp = None

    async def get(self, refresh_fn: OnAction):

        async with self._lock:
            if not self._last_cache_timestamp or \
                    asyncio.get_event_loop().time() - self._last_cache_timestamp > self._expire_time:
                logging.debug('Cache refresh time expired, so call cache refresher function and reset the cache')
                self._last_cache_timestamp = asyncio.get_event_loop().time()
                await self._set_cache(await refresh_fn())
            else:
                logging.debug('Cache refresh time is not expired, so return data from cache')

        return await self._get_cache()

    @abstractmethod
    async def _set_cache(self, cache: Any):
        return

    @abstractmethod
    async def _get_cache(self) -> Any:
        return


class LocalCache(CacheBase):
    async def _get_cache(self) -> Any:
        logging.debug(f'LocalCache: get_cache function called. Cached data: {self._cache}')
        return self._cache

    async def _set_cache(self, cache: Any):
        logging.debug(f'LocalCache: set_cache function called. Refreshed cache data: {self._cache}')
        self._cache = cache


# Implement Global cache using redis server, which is used between multiple fx conversion services are running
class RedisCache(CacheBase):
    async def _get_cache(self) -> Any:
        logging.debug('RedisCache::_get_cache function called')
        return self._cache

    async def _set_cache(self, cache: Any):
        logging.debug('RedisCache::_set_cache function called')
        self._cache = cache


async def main():
    from functools import partial
    from time import sleep

    async def increment(value=0):
        return value+1

    cache = LocalCache(expire_time=1)
    assert (await cache.get(partial(increment, 1)) == 2)
    assert (await cache.get(partial(increment, 2)) == 2)
    sleep(1)
    assert (await cache.get(partial(increment, 3)) == 4)
    assert (await cache.get(partial(increment, 4)) == 4)
    sleep(1)
    assert (await cache.get(partial(increment, 4)) == 5)

if __name__ == '__main__':
    asyncio.run(main())


