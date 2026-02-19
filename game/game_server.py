import asyncio
import time
from typing import TypeAlias

import pygame

from framework.protobufs.compiled_protobufs.game_pb2 import *
from wrappers.server_wrapper import QuicServer

"""

TODO:

add delta time calcs

"""

SERVER_FPS: int = 30

SERVER_IP: str = '127.0.0.1'
SERVER_PORT: int = 8080

PLAYER_SPEED = 3

ConnectionId: TypeAlias = int


class ServerPlayer:

    def __init__(self, player_id: int):
        self._pos = pygame.math.Vector2()
        self._id = player_id

    def update_pos(self, direction: pygame.Vector2):
        self._pos += direction * PLAYER_SPEED

    def get_pos(self):
        return self._pos

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
        self.players: dict[ConnectionId, ServerPlayer] = {}
        self.delta_time = 0
        self.last_time = 0

    def build_response(self):

        state_list = ServerPlayerStateList()

        for player in self.players.values():
            p = state_list.players.add()
            p.playerId = player.get_player_id()
            p.positionX = int(player.get_pos().x)
            p.positionY = int(player.get_pos().y)

        return state_list.SerializeToString()

    def on_receive(self, connection_id: int, data: bytes):

        request = ClientPlayerState()
        request.ParseFromString(data)

        player = self.players.get(connection_id)
        if not player:
            return

        player.update_pos(pygame.Vector2(request.directionX, request.directionY))

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
                self.server.broadcast(self.build_response())
                self.delta_time = time.monotonic() - self.last_time
                self.last_time = time.monotonic()
                await asyncio.sleep(1 / SERVER_FPS)

        finally:
            print("Shutting down")
            self.server.stop()


if __name__ == '__main__':
    game = GameServer(ip=SERVER_IP, port=SERVER_PORT)
    asyncio.run(game.run())
