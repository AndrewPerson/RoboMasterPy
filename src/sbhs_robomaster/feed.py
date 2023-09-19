from typing import Generic, TypeVar, AsyncIterator
import asyncio
from weakref import WeakSet
from .dropping_async_enumerable import DroppingAsyncEnumerable


FeedT = TypeVar("FeedT")
class Feed(Generic[FeedT]):
    """
    Used for expressing a constant stream of data.

    Internally, this is implemented as an async iterator.

    Example:
    ```py
    import asyncio
    from sbhs_robomaster import Feed

    feed = Feed()

    async def send_data():
        for i in range(5):
            await feed.feed(i)
            await asyncio.sleep(1)

    async def receive_data():
        async for data in feed: # This will run forever as feeds are never closed.
            print(data)
    
    # Run both coroutines concurrently
    asyncio.run(asyncio.gather(send_data(), receive_data()))

    # Prints:
    # 0
    # 1
    # 2
    # 3
    # 4
    ```

    Feeds can be used to implement push-based data streams. For example, the RoboMaster robot
    sends data over UDP to the computer. This data can be received using the `Feed` class:

    ```py
    from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP, LineColour

    async def main():
        async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
            await robot.set_line_recognition_enabled()
            await robot.set_line_recognition_color(LineColour.Red)

            async for line in robot.line:
                print(line.type)

    asyncio.run(main())
    ```

    To stop receiving data, just `break` out of the loop.

    **NOTE:** Data in a feed may arrive faster than it can be consumed. This means that
    you may get delayed results. You probably want to use `.dropping_async_enumerable.DroppingAsyncEnumerable` to help
    with this.

    **NOTE:** Data sent to a feed *before* it is iterated over won't appear in the iteration.
    """

    _iterators: WeakSet["FeedIterator[FeedT]"]

    def __init__(self):
        self._iterators = WeakSet()

    async def feed(self, data: FeedT) -> None:
        """
        Send data to all consumers of this feed.

        This must be awaited as internally this uses an async lock.
        """
        await asyncio.gather(*[iterator._feed(data) for iterator in self._iterators])

    def __aiter__(self):
        iterator = FeedIterator()
        self._iterators.add(iterator)
        return iterator


FeedIterT = TypeVar("FeedIterT")
class FeedIterator(Generic[FeedIterT], AsyncIterator[FeedIterT]):
    """@private"""

    _queued_data: list[FeedIterT]
    _data_lock: asyncio.Lock
    _recv_data_flag: asyncio.Event

    def __init__(self):
        self._queued_data = []
        self._data_lock = asyncio.Lock()
        self._recv_data_flag = asyncio.Event()

    async def _feed(self, data: FeedIterT):
        async with self._data_lock:
            self._queued_data.append(data)
            self._recv_data_flag.set()

    async def __anext__(self):
        if len(self._queued_data) > 0:
            result = self._queued_data.pop(0)

            if len(self._queued_data) == 0:
                self._recv_data_flag.clear()

            return result
        else:
            await self._recv_data_flag.wait()
            return await self.__anext__()
