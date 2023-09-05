import asyncio
from io import BytesIO
from socketserver import BaseServer, UDPServer, DatagramRequestHandler
from data import Response
from feed import Feed

class PushReceiver:
    conn: UDPServer

    feed: Feed[Response] = Feed()

    def __init__(self, ip: str, port: int):
        self.conn = UDPServer(
            (ip, port),
            lambda request, client_address, server: PushReceiverHandler(self.feed, request, client_address, server)
        )

    async def push_handler(self, request):
        packet, _ = request
        read = BytesIO(packet)

        await self.feed.feed(Response(read.read().decode().split(" ")))


class PushReceiverHandler(DatagramRequestHandler):
    feed: Feed[Response]

    def __init__(self, feed: Feed[Response], request, client_address, server: BaseServer) -> None:
        super().__init__(request, client_address, server)

        self.feed = feed

    def handle(self):
        asyncio.create_task(self.feed.feed(Response(self.rfile.read().decode()[:-1].split(" "))))
