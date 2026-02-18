import asyncio
import struct
import time

import pygame

from ..wrappers.server_wrapper import QuicServer

SERVER_FPS: int = 30

"""

TODO:

add delta time calcs

"""

SERVER_IP: str = '127.0.0.1'
SERVER_PORT: int = 8080

PLAYER_SPEED = 3


class ServerPlayer:

    def __init__(self, player_id: int):
        self._pos = pygame.math.Vector2()
        self._id = player_id

    def update_pos(self, direction: pygame.Vector2):
        self._pos += direction * PLAYER_SPEED

    def get_pos(self):
        return int(self._pos.x), int(self._pos.y)

    def get_player_id(self):
        return self._id


class GameServer:

    def __init__(self, ip: str, port: int):
        self.server = QuicServer(
            ip=ip,
            port=port,
            cert_file="../certificate/cert.pem",
            key_file="../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.lifetime_connections = 0
        self.players: dict[int, ServerPlayer] = {}
        self.delta_time = 0
        self.last_time = 0

    def serialize(self):
        buf = bytearray()

        changed_players = [p for p in self.players.values()]
        buf += struct.pack('H', len(changed_players))

        for p in changed_players:
            x, y = p.get_pos()
            buf += struct.pack('Hhh', p.get_player_id(), x, y)

        return bytes(buf)

    def deserialize(self, data: bytes):

        if len(data) < struct.calcsize('B'):
            return None

        value = struct.unpack('B', data[:1])[0]

        x = ((value >> 2) & 0b11) - 1
        y = (value & 0b11) - 1

        return pygame.math.Vector2(x, y)

    def on_receive(self, connection_id: int, data: bytes):

        player_direction = self.deserialize(data)
        if player_direction:

            player = self.players.get(connection_id)
            if player:
                player.update_pos(player_direction)

    def on_connect(self, connection_id: int):

        print(f"{connection_id} connected")
        player = ServerPlayer(self.lifetime_connections)
        self.lifetime_connections += 1
        self.players[connection_id] = player

    def on_disconnect(self, connection_id: int):

        print(f"{connection_id} disconnected")
        self.players.pop(connection_id)

    async def run(self):
        await self.server.start()
        print('server is running')

        try:
            while True:
                await self.server.broadcast(self.serialize())
                await asyncio.sleep(1 / SERVER_FPS)
                self.delta_time = time.monotonic() - self.last_time
                self.last_time = time.monotonic()

        finally:
            print("Shutting down")
            await self.server.stop()


if __name__ == '__main__':
    game = GameServer(ip=SERVER_IP, port=SERVER_PORT)
    asyncio.run(game.run())
