from typing import Any
import asyncio
from .data import Response

class AutoConnectProtocol(asyncio.DatagramProtocol):
    ip_future: asyncio.Future[str]

    def __init__(self) -> None:
        super().__init__()

        self.ip_future = asyncio.get_event_loop().create_future()

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        if not self.ip_future.done():
            # Format: robot ip <ip>;
            message = Response(data.decode()[:-1].split(" "))

            self.ip_future.set_result(message.get_str(2))
