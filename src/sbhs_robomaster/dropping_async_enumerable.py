from typing import Generic, TypeVar, AsyncIterable
import asyncio


DroppingAsyncEnumerableT = TypeVar("DroppingAsyncEnumerableT")
class DroppingAsyncEnumerable(Generic[DroppingAsyncEnumerableT]):
    """
    Used to prevent data queuing up in an async iterator (usually a `.feed.Feed`) if the consumer is slow.

    This is implemented as an async iterator.

    Example:
    ```py
    from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP, LineColour, DroppingAsyncEnumerable

    async def main():
        async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
            await robot.set_line_recognition_enabled()
            await robot.set_line_recognition_color(LineColour.Red)

            # Now, any line data that arrives while the consumer is sleeping will be dropped.
            async for line in DroppingAsyncEnumerable(robot.line):
                print(line.type)
                await asyncio.sleep(0.1) # Simulate a slow consumer

    asyncio.run(main())
    ```
    """

    _enumerable: AsyncIterable[DroppingAsyncEnumerableT]
    _current: DroppingAsyncEnumerableT
    _current_flag: asyncio.Event
    _poll_task: asyncio.Task
    _done: bool = False

    def __init__(self, enumerable: AsyncIterable[DroppingAsyncEnumerableT]):
        self._enumerable = enumerable

        self._current_flag = asyncio.Event()

        self._poll_task = asyncio.create_task(self._poll_current())

    async def _poll_current(self):
        async for value in self._enumerable:
            self._current = value
            self._current_flag.set()

        self._done = True
        self._current_flag.set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self._current_flag.wait()
        self._current_flag.clear()

        if self._done:
            raise StopAsyncIteration()

        return self._current

    def __del__(self):
        self._poll_task.cancel()
