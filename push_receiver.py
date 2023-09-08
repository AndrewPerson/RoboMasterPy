import asyncio
from data import Response
from feed import Feed

class PushReceiver:
    data_receiving_task: asyncio.Task

    feed: Feed[Response] = Feed()

    def __init__(self, ip: str, port: int):
        loop = asyncio.get_event_loop()
        
        asyncio.create_task(
            loop.create_datagram_endpoint(PushReceiverHandler, local_addr=('0.0.0.0', port))
        ).add_done_callback(self.create_data_receiver)

    def create_data_receiver(self, tup: asyncio.Task[tuple[asyncio.DatagramTransport, "PushReceiverHandler"]]):
        self.data_receiving_task = asyncio.create_task(self.receive_data(tup.result()[1].feed))

    async def receive_data(self, feed: Feed[bytes]):
        async for message in feed:
            await self.feed.feed(Response(message.decode()[:-1].split(" ")))

    def __del__(self):
        self.data_receiving_task.cancel()


class PushReceiverHandler(asyncio.DatagramProtocol):
    feed: Feed[bytes] = Feed()
    feed_tasks: set[asyncio.Task] = set()

    def __init__(self) -> None:
        super().__init__()

    def datagram_received(self, data, addr):
        t = asyncio.create_task(self.feed.feed(data))
        self.feed_tasks.add(t)
        t.add_done_callback(self.feed_tasks.discard)