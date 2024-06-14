"""
@private
"""

import asyncio
from .data import Response
from .feed import Feed


class PushReceiver:
    feed: Feed[Response]

    _data_receiving_task: asyncio.Task[None]

    def __init__(self, port: int):
        self.feed = Feed()

        loop = asyncio.get_event_loop()
        
        asyncio.create_task(
            loop.create_datagram_endpoint(_PushReceiverHandler, local_addr=('0.0.0.0', port))
        ).add_done_callback(self._create_data_receiver)

    def _create_data_receiver(self, tup: asyncio.Task[tuple[asyncio.DatagramTransport, "_PushReceiverHandler"]]):
        self._data_receiving_task = asyncio.create_task(self._receive_data(tup.result()[1].feed))

    async def _receive_data(self, feed: Feed[bytes]):
        while True:
            message = await feed.get()
            self.feed.feed(Response(message.decode()[:-1].split(" ")))

    def __del__(self):
        self._data_receiving_task.cancel()


class _PushReceiverHandler(asyncio.DatagramProtocol):
    feed: Feed[bytes]

    def __init__(self) -> None:
        super().__init__()

        self.feed = Feed()

    def datagram_received(self, data: bytes, addr: tuple[str, int]):
        self.feed.feed(data)
