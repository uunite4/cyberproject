import asyncio
import time
from typing import TypeAlias

from pygame import Vector2

from protobufs.compiled_protobufs.game_pb2 import *
from wrappers.server_wrapper import QuicServer

"""

TODO:

"""

SERVER_FPS: int = 30

SERVER_IP: str = '127.0.0.1'
SERVER_PORT: int = 8080

PLAYER_SPEED = 5

ConnectionId: TypeAlias = int


class ServerPlayer:

    def __init__(self, player_id: int):
        self._pos: Vector2 = Vector2()
        self._id: int = player_id

    def update_pos(self, direction: Vector2):
        self._pos += direction * PLAYER_SPEED * 1

    def get_pos(self):
        return self._pos

    def get_player_id(self):
        return self._id


class GameServer:

    def __init__(self, ip: str, port: int):
        self.server = QuicServer(
            ip=ip,
            port=port,
            cert_file="../../certificate/cert.pem",
            key_file="../../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.lifetime_connections = 0
        self.players: dict[ConnectionId, ServerPlayer] = {}
        self.delta_time = 0
        self.last_tick_time = 0

    def broadcast(self):

        state_list = ServerPlayerStateList()

        for player in self.players.values():
            p = state_list.players.add()
            p.playerId = player.get_player_id()
            p.positionX = int(player.get_pos().x)
            p.positionY = int(player.get_pos().y)

        self.server.broadcast(state_list.SerializeToString())

    def on_receive(self, connection_id: int, data: bytes):

        request = ClientPlayerState()
        request.ParseFromString(data)

        player = self.players.get(connection_id)
        if not player:
            return

        player_pos = Vector2(request.directionX, request.directionY)
        player.update_pos(player_pos)

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
        print('Server running')

        try:
            while True:
                self.broadcast()

                now = time.monotonic()
                self.delta_time = now - self.last_tick_time
                self.last_tick_time = now

                await asyncio.sleep(1 / SERVER_FPS)

        finally:
            print("Shutting down")
            await self.server.stop()


if __name__ == '__main__':
    game = GameServer(ip=SERVER_IP, port=SERVER_PORT)
    asyncio.run(game.run())
