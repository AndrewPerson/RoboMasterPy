from .feed import Feed
from typing import Generic, TypeVar
import asyncio


DroppingFeedT = TypeVar("DroppingFeedT")
class DroppingFeed(Generic[DroppingFeedT]):
    """
    Used to prevent data queuing up in a `.feed.Feed` if the consumer is slow.

    Example:
    ```py
    import asyncio
    from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP, LineColour, DroppingFeed

    async def main():
        async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
            await robot.set_line_recognition_enabled()
            await robot.set_line_recognition_color(LineColour.Red)

            # Now, any line data that arrives while the consumer is sleeping will be dropped.
            dropping_line = DroppingFeed(robot.line)

            while True:
                print(await dropping_line.get_most_recent())
                await asyncio.sleep(0.1) # Simulate a slow consumer

    asyncio.run(main())
    ```
    """

    _feed: Feed[DroppingFeedT]
    _current: DroppingFeedT
    _current_flag: asyncio.Event
    _poll_task: asyncio.Task[None]

    def __init__(self, feed: Feed[DroppingFeedT]):
        self._feed = feed

        self._current_flag = asyncio.Event()

        self._poll_task = asyncio.create_task(self._poll_current())

    async def get_most_recent(self) -> DroppingFeedT:
        """
        Gets the most recent piece of data.

        If no data has been received yet, this will block until data is received.

        Note: 2 clients calling this method will receive the same data.
        """
        await self._current_flag.wait()
        self._current_flag.clear()
        return self._current

    async def _poll_current(self):
        while True:
            self._current = await self._feed.get()
            self._current_flag.set()
