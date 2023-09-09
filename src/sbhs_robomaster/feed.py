from typing import Generic, TypeVar
import asyncio

FeedT = TypeVar("FeedT")
class Feed(Generic[FeedT]):
    queued_data: list[FeedT] = []
    data_lock: asyncio.Lock = asyncio.Lock()
    recv_data_flag: asyncio.Event = asyncio.Event()

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
