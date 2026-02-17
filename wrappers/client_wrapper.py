from typing import Callable

from qh3 import QuicConnectionProtocol, QuicConfiguration, connect
from qh3.quic.events import StreamDataReceived, ConnectionTerminated

OnReceive = Callable[[int, bytes], None]


class _ClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client: "QuicClient", connection_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = client
        self._connection_id = connection_id
        self._stream_id = self._quic.get_next_available_stream_id()

    def send(self, data: bytes):
        self._quic.send_stream_data(self._stream_id, data, end_stream=False)
        self.transmit()

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            self._client.on_receive(self._connection_id, event.data)

        elif isinstance(event, ConnectionTerminated):
            self.close()

    def close(self):
        self._client.close_connection(self._connection_id)
        self._quic.close(error_code=0)
        self.transmit()


class QuicClient:
    def __init__(self, cert_file: str, on_receive: OnReceive):
        self.cert_file = cert_file
        self.on_receive = on_receive

        self._connections: dict[int, _ClientProtocol] = {}
        self.lifetime_connections = 0

    async def connect(self, server_ip: str, server_port: int):
        config = QuicConfiguration(is_client=True)
        config.load_verify_locations(cafile=self.cert_file)
        config.server_name = server_ip

        connection_id = self._get_next_connection_id()

        def create_protocol(*args, **kwargs):
            return _ClientProtocol(
                *args,
                client=self,
                connection_id=connection_id,
                **kwargs,
            )

        connection_context_manager = connect(
            host=server_ip,
            port=server_port,
            configuration=config,
            create_protocol=create_protocol

        )

        protocol = await connection_context_manager.__aenter__()
        protocol.connection = connection_context_manager

        self._add_connection(connection_id, protocol)

        print(f'{server_ip}:{server_port} connected')
        return connection_id

    def send(self, connection_id: int, data: bytes):
        conn = self._get_connection(connection_id)
        if not conn:
            raise RuntimeError("Not connected")
        conn.send(data)

    async def close_connection(self, connection_id: int):
        conn = self._get_connection(connection_id)
        if conn:
            conn.close()

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
        connection_id = self.lifetime_connections
        self.lifetime_connections += 1
        return connection_id
