from typing import Callable

from qh3 import QuicConnectionProtocol, QuicConfiguration, serve
from qh3.quic.events import (
    StreamDataReceived,
    ConnectionTerminated,
    ProtocolNegotiated,
)

OnReceive = Callable[[int, bytes], None]
OnConnect = Callable[[int], None]
OnDisconnect = Callable[[int], None]


class _ServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, server: "QuicServer", connection_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = server
        self._connection_id = connection_id
        self._stream_id = self._quic.get_next_available_stream_id()

    def send(self, data: bytes):
        self._quic.send_stream_data(self._stream_id, data, end_stream=False)
        self.transmit()

    def quic_event_received(self, event):
        if isinstance(event, ProtocolNegotiated):
            self._server.on_connect(self._connection_id)

        elif isinstance(event, StreamDataReceived):
            self._server.on_receive(self._connection_id, event.data)

        elif isinstance(event, ConnectionTerminated):
            self.close()

    def close(self):
        self._server._remove_connection(self._connection_id)
        self._server.on_disconnect(self._connection_id)
        self._quic.close(error_code=0)
        self.transmit()


class QuicServer:
    def __init__(
            self, ip: str, port: int,
            cert_file: str, key_file: str,
            on_receive: OnReceive,
            on_connect: OnConnect,
            on_disconnect: OnDisconnect,
    ):
        self.ip = ip
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file

        self.on_receive = on_receive
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self._server = None
        self._connections: dict[int, _ServerProtocol] = dict()
        self.lifetime_connections = 0

    async def broadcast(self, data: bytes):
        for conn in list(self._connections.values()):
            conn.send(data)

    async def send(self, data: bytes, connection_id: int):
        connection = self._get_connection(connection_id)
        if not connection:
            raise RuntimeError("Not connected")
        connection.send(data)

    def _get_next_connection_id(self) -> int:
        connection_id = self.lifetime_connections
        self.lifetime_connections += 1
        return connection_id

    def _add_connection(self, connection_id: int, conn: _ServerProtocol):
        self._connections[connection_id] = conn

    def _get_connection(self, connection_id: int):
        return self._connections.get(connection_id)

    def _remove_connection(self, connection_id: int):
        self._connections.pop(connection_id, None)

    async def start(self):
        config = QuicConfiguration(is_client=False)
        config.load_cert_chain(self.cert_file, self.key_file)

        def create_connection(*args, **kwargs):
            connection_id = self._get_next_connection_id()
            connection = _ServerProtocol(
                *args,
                server=self,
                connection_id=connection_id,
                **kwargs,
            )
            self._add_connection(connection_id, connection)
            return connection

        self._server = await serve(
            host=self.ip,
            port=self.port,
            configuration=config,
            create_protocol=create_connection,
        )

    async def stop(self):
        self._server.close()
