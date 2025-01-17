import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Any
from config import Settings

OnAction = Callable[..., Awaitable[Any]]
logging.basicConfig(format=Settings.log.format)
logging.root.setLevel(Settings.log.level)


class CacheBase(ABC):
    """
    Abstract base class for implementing caching mechanisms with cache refresh.

    Methods:
        reset():
            Resets the cache by clearing the last cache timestamp, forcing a refresh on the next `get` call.

        get(refresh_fn: OnAction) -> Any:
            Retrieves data from the cache. If the cache is expired or uninitialized, calls the provided refresh
            function to fetch new data and update the cache.

    Usage:
        - Subclasses should implement `_set_cache` and `_get_cache` to define how the cache is stored and retrieved.
        - Use the `get` method to safely access or refresh cached data.

    Notes:
        - The `refresh_time` parameter allows customization of the cache expiration duration.
        - Concurrency is handled using an asyncio lock to prevent race conditions during cache updates.
    """
    def __init__(self, refresh_time=3600):
        self._lock = asyncio.Lock()
        self._refresh_time = refresh_time
        self._cache = None
        self._last_cache_timestamp = None

    async def reset(self):
        self._last_cache_timestamp = None

    async def get(self, refresh_fn: OnAction):

        async with self._lock:
            if not self._last_cache_timestamp or \
                    asyncio.get_event_loop().time() - self._last_cache_timestamp > self._refresh_time:
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
    """
    A local in-memory cache implementation for storing data within a single service instance.

    Methods:
        _get_cache() -> Any:
            Retrieves the current cached data. Returns `None` if no data is cached.

        _set_cache(cache: Any):
            Updates the cached data with the provided value.

    Notes:
        This cache works with in single process it is not shared across other processes or instances of this service.
    """
    async def _get_cache(self) -> Any:
        logging.debug(f'LocalCache: get_cache function called. Cached data: {self._cache}')
        return self._cache

    async def _set_cache(self, cache: Any):
        logging.debug(f'LocalCache: set_cache function called. Refreshed cache data: {self._cache}')
        self._cache = cache


class RedisCache(CacheBase):
    """
    A global cache implementation using a Redis server for shared caching across multiple processes and/or service instances.

    Methods:
        _get_cache() -> Any:
            Retrieves the current cached data from the Redis server.

        _set_cache(cache: Any):
            Updates the cached data on the Redis server with the provided value.

    Notes:
        TODO: Yet to implement this feature
        This cache is designed for distributed environments where multiple instances of the
        FX conversion service are running and need to share a consistent cache.
    """
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

    cache = LocalCache(refresh_time=1)
    assert (await cache.get(partial(increment, 1)) == 2)
    assert (await cache.get(partial(increment, 2)) == 2)
    sleep(1)
    assert (await cache.get(partial(increment, 3)) == 4)
    assert (await cache.get(partial(increment, 4)) == 4)
    sleep(1)
    assert (await cache.get(partial(increment, 4)) == 5)

if __name__ == '__main__':
    asyncio.run(main())


