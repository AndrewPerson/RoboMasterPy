from typing import Generic, TypeVar, AsyncIterable
import asyncio


DroppingAsyncEnumerableT = TypeVar("DroppingAsyncEnumerableT")
class DroppingAsyncEnumerable(Generic[DroppingAsyncEnumerableT]):
    enumerable: AsyncIterable[DroppingAsyncEnumerableT]
    current: DroppingAsyncEnumerableT
    current_flag: asyncio.Event
    poll_task: asyncio.Task
    done: bool = False

    def __init__(self, enumerable: AsyncIterable[DroppingAsyncEnumerableT]):
        self.enumerable = enumerable

        self.current_flag = asyncio.Event()

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
