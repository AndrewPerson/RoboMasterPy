from typing import Generic, TypeVar, AsyncIterator
import asyncio
from weakref import WeakSet


FeedT = TypeVar("FeedT")
class Feed(Generic[FeedT]):
    iterators: WeakSet["FeedIterator[FeedT]"]

    def __init__(self):
        self.iterators = WeakSet()

    async def feed(self, data: FeedT):
        await asyncio.gather(*[iterator._feed(data) for iterator in self.iterators])

    def __aiter__(self):
        iterator = FeedIterator()
        self.iterators.add(iterator)
        return iterator


FeedIterT = TypeVar("FeedIterT")
class FeedIterator(Generic[FeedIterT], AsyncIterator[FeedIterT]):
    queued_data: list[FeedIterT]
    data_lock: asyncio.Lock
    recv_data_flag: asyncio.Event

    def __init__(self):
        self.queued_data = []
        self.data_lock = asyncio.Lock()
        self.recv_data_flag = asyncio.Event()

    async def _feed(self, data: FeedIterT):
        async with self.data_lock:
            self.queued_data.append(data)
            self.recv_data_flag.set()

    async def __anext__(self):
        if len(self.queued_data) > 0:
            result = self.queued_data.pop(0)

            if len(self.queued_data) == 0:
                self.recv_data_flag.clear()

            return result
        else:
            await self.recv_data_flag.wait()
            return await self.__anext__()
