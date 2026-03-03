import asyncio
from aioquic.asyncio import connect, QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived, ConnectionIdIssued


class QUICClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._response_waiter = None

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            if self._response_waiter and not self._response_waiter.done():
                self._response_waiter.set_result(event.data)

    async def send_request(self, data: bytes):
        self._response_waiter = asyncio.Future()

        # Open a bidirectional stream
        stream_id = self._quic.get_next_available_stream_id()

        # We send with end_stream=True.
        # This tells the server "I am done sending, now your turn".
        self._quic.send_stream_data(stream_id, data + b"\n", end_stream=True)
        self.transmit()

        return await self._response_waiter


class EasyQUIC:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.configuration = QuicConfiguration(is_client=True)
        self.configuration.verify_mode = False
        self.configuration.alpn_protocols = ["demo"]
        self.connection = None

    async def connect(self):
        # Entering the context manager to get the protocol
        self._cm = connect(
            self.host, self.port,
            configuration=self.configuration,
            create_protocol=QUICClientProtocol
        )
        self.connection = await self._cm.__aenter__()
        return self.connection

    async def send(self, message):
        if (type(message) is str):
            message = message.encode()

        response = await self.connection.send_request(message)
        return response
    async def close(self):
        if self._cm:
            await self._cm.__aexit__(None, None, None)


# ----------
# SERVER
# ----------

class QUICServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        self.handler = kwargs.pop("handler", None)
        super().__init__(*args, **kwargs)
        self.storage = {}

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            s_id = event.stream_id
            if s_id not in self.storage: self.storage[s_id] = b""
            self.storage[s_id] += event.data

            # Trigger logic when message is complete
            if b"\n" in self.storage[s_id] or event.end_stream:
                # request_text = self.storage[s_id].strip().decode()
                request_text = self.storage[s_id].strip()

                if self.handler:
                    response = self.handler(request_text)
                    # IMPORTANT: Send on the SAME s_id.
                    # QUIC allows replying on the same bidirectional stream.
                    if (type(response) is str):
                        response = response.encode()
                    self._quic.send_stream_data(s_id, response, end_stream=True)
                    self.transmit()

                del self.storage[s_id]


class EasyQUICServer:
    def __init__(self, host, port, cert_file, key_file):
        self.host = host
        self.port = port
        self.config = QuicConfiguration(is_client=False)
        self.config.load_cert_chain(cert_file, key_file)
        self.config.alpn_protocols = ["demo"]

    async def start(self, logic_function):
        await serve(
            self.host, self.port,
            configuration=self.config,
            create_protocol=lambda *args, **kwargs: QUICServerProtocol(
                *args, handler=logic_function, **kwargs
            )
        )
        print(f"Server listening on {self.host}:{self.port}")
        await asyncio.Future()