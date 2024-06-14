from typing import Generic, TypeVar
import asyncio


FeedT = TypeVar("FeedT")
class Feed(Generic[FeedT]):
    """
    Used for expressing a constant stream of data.

    To get the next piece of data, call `get`.

    Example:
    ```py
    import asyncio
    from sbhs_robomaster import Feed

    feed = Feed()

    async def send_data():
        for i in range(5):
            feed.feed(i)
            await asyncio.sleep(1)

    async def receive_data():
        while True:
            print(await feed.get())
    
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

            while True:
                print(await robot.line.get())

    asyncio.run(main())
    ```

    **NOTE:** Data in a feed may arrive faster than it can be consumed. This means that
    you may get delayed results. You probably want to use `.dropping_feed.DroppingFeed` to help
    with this.

    **NOTE:** Data sent to a feed *before* `get` is called won't be returned.
    """

    _return_futures: set[asyncio.Future[FeedT]]

    def __init__(self):
        self._return_futures = set()

    def feed(self, data: FeedT) -> None:
        """
        Send data to all consumers of this feed.
        """
        for future in self._return_futures:
            future.set_result(data)

        self._return_futures.clear()

    def get(self) -> asyncio.Future[FeedT]:
        """
        Get the next piece of data from this feed.
        """
        future = asyncio.get_event_loop().create_future()
        self._return_futures.add(future)
        return future
