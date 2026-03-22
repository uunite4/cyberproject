import asyncio
import time
import uuid
from typing import Callable

from qh3 import QuicConnectionProtocol, QuicConfiguration, connect
from qh3.quic.events import StreamDataReceived, ConnectionTerminated

OnReceive = Callable[[int, bytes], None]

IDLE_TIMEOUT_SECONDS = 60
KEEP_ALIVE_INTERVAL_SECONDS = 20


class _ClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client: "QuicClient", connection_id: int, connection_cm, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = client
        self._connection_id = connection_id
        self._connection_cm = connection_cm
        self._stream_id = self._quic.get_next_available_stream_id()
        self._ping_task = asyncio.create_task(self._keepalive())

    def send(self, data: bytes):
        self._quic.send_stream_data(self._stream_id, data, end_stream=False)
        self.transmit()

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            self._client.on_receive(self._connection_id, event.data)

        elif isinstance(event, ConnectionTerminated):
            self._client._remove_connection(self._connection_id)

    async def close_protocol(self):
        self._ping_task.cancel()
        self._client._remove_connection(self._connection_id)

        self._quic.close(error_code=0)
        self.transmit()
        await self._connection_cm.__aexit__(None, None, None)

    async def _keepalive(self):
        while True:
            await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)
            self._quic.send_ping(time.monotonic_ns())
            self.transmit()


class QuicClient:
    def __init__(self, on_receive: OnReceive):
        self.on_receive = on_receive

        self._connections: dict[int, _ClientProtocol] = {}
        self.lifetime_connections = 0

    async def connect(self, server_ip: str, server_port: int):
        config = QuicConfiguration(is_client=True, idle_timeout=IDLE_TIMEOUT_SECONDS,
                                   verify_mode=False, server_name=server_ip)

        connection_id = self._get_next_connection_id()
        connection_context_manager = connect(
            host=server_ip,
            port=server_port,
            configuration=config,
            create_protocol=lambda *args, **kwargs: _ClientProtocol(
                *args,
                client=self,
                connection_id=connection_id,
                connection_cm=connection_context_manager,
                **kwargs,
            ),
        )

        client_protocol = await connection_context_manager.__aenter__()
        client_protocol._connection_cm = connection_context_manager

        self._add_connection(connection_id, client_protocol)
        return connection_id

    def send(self, connection_id: int, data: bytes):
        conn = self._get_connection(connection_id)
        if not conn:
            print(f"{connection_id} Not connected")
            return
        conn.send(data)

    def broadcast(self, data: bytes):
        for conn in list(self._connections.values()):
            conn.send(data)

    async def close_connection(self, connection_id: int):
        conn = self._get_connection(connection_id)
        if conn:
            await conn.close_protocol()
            self._remove_connection(connection_id)

    async def stop(self):
        for conn_id in list(self._connections.keys()):
            await self.close_connection(conn_id)

    def _add_connection(self, connection_id: int, conn: _ClientProtocol):
        self._connections[connection_id] = conn

    def _get_connection(self, connection_id: int):
        return self._connections.get(connection_id)

    def _remove_connection(self, connection_id: int):
        self._connections.pop(connection_id, None)

    def _get_next_connection_id(self) -> int:
        return uuid.uuid4().int
