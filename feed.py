from typing import Generic, TypeVar, AsyncGenerator
import asyncio

FeedT = TypeVar("FeedT")
class Feed(Generic[FeedT], AsyncGenerator[FeedT, None]):
    queued_data: list[FeedT]
    data_lock: asyncio.Lock
    recv_data_flag: asyncio.Event

    def __init__(self):
        self.queued_data = []
        self.data_lock = asyncio.Lock()
        self.recv_data_flag = asyncio.Event()

    async def feed(self, data: FeedT):
        await self.data_lock.acquire()

        self.queued_data.append(data)
        self.recv_data_flag.set()

        self.data_lock.release()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if len(self.queued_data) > 0:
            result = self.queued_data.pop(0)

            if len(self.queued_data) == 0:
                self.recv_data_flag.clear()

            return result
        else:
            await self.recv_data_flag.wait()
            return await self.__anext__()
