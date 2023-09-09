from typing import Generic, TypeVar, AsyncGenerator
import asyncio


DroppingAsyncEnumerableT = TypeVar("DroppingAsyncEnumerableT")
class DroppingAsyncEnumerable(Generic[DroppingAsyncEnumerableT], AsyncGenerator[DroppingAsyncEnumerableT, None]):
    enumerable: AsyncGenerator[DroppingAsyncEnumerableT, None]
    current: DroppingAsyncEnumerableT
    current_flag: asyncio.Event = asyncio.Event()
    poll_task: asyncio.Task
    done: bool = False

    def __init__(self, enumerable: AsyncGenerator[DroppingAsyncEnumerableT, None]):
        self.enumerable = enumerable

        self.poll_task = asyncio.create_task(self._poll_current())

    async def _poll_current(self):
        async for value in self.enumerable:
            self.current = value
            self.current_flag.set()

        self.done = True
        self.current_flag.set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self.current_flag.wait()
        self.current_flag.clear()

        if self.done:
            raise StopAsyncIteration()

        return self.current

    def __del__(self):
        self.poll_task.cancel()