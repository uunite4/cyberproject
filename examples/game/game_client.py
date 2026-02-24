import asyncio

import pygame
from pygame import Vector2

from examples.game.game_server import SERVER_IP, SERVER_PORT
from protobufs.compiled_protobufs.game_pb2 import *
from wrappers.client_wrapper import QuicClient

DISPLAY_FPS: int = 60
SEND_FPS: int = 20

WIDTH: int = 320 * 2
HEIGHT: int = 200 * 2

"""

skip interpolating own player - maybe

add lerp between last position - must

instead of using "server_tick" to control the send fps,
made a new task that runs at the given fps

build a networking framework - on it

"""


class ClientPlayer(pygame.sprite.Sprite):
    def __init__(self, pos: Vector2, group):
        super().__init__(group)
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=pos)

    def set_pos(self, pos: Vector2):
        self.rect.topleft = pos


class GameClient:

    def __init__(self, cert_file):
        self.running = True
        self.server_id = None
        self.client = QuicClient(cert_file=cert_file, on_receive=self.on_receive)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.players: dict[int, ClientPlayer] = {}
        self.sprite_group = pygame.sprite.Group()

        self.player_pos: Vector2 = Vector2()
        self.player_direction: Vector2 = Vector2()
        self.tick: int = 0

    def send(self):
        request = ClientPlayerState(
            directionX=int(self.player_direction.x),
            directionY=int(self.player_direction.y)
        )
        self.client.send(self.server_id, request.SerializeToString())

    def upsert_player(self, player_id: int, pos: Vector2):
        if player_id in self.players:
            player = self.players[player_id]
            player.set_pos(pos)
            return player

        player = ClientPlayer(pos, self.sprite_group)
        self.players[player_id] = player
        return player

    def on_receive(self, connection_id: int, data: bytes):
        if connection_id == self.server_id:

            state_list = ServerPlayerStateList()
            state_list.ParseFromString(data)

            for player in state_list.players:
                self.upsert_player(
                    player.playerId,
                    Vector2(player.positionX, player.positionY)
                )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update_player_direction(self):
        keys = pygame.key.get_pressed()

        direction = Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y = -1
        if keys[pygame.K_s]:
            direction.y = 1
        if keys[pygame.K_a]:
            direction.x = -1
        if keys[pygame.K_d]:
            direction.x = 1

        self.player_direction = direction

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.sprite_group.draw(self.screen)
        pygame.display.update()

    def update_game(self):
        self.handle_events()
        self.update_player_direction()
        self.draw()

    async def game_loop(self):
        while self.running:
            self.tick += 1
            self.update_game()
            await asyncio.sleep(1 / DISPLAY_FPS)

    async def send_loop(self):
        while self.running:
            self.send()
            await asyncio.sleep(1 / SEND_FPS)

    async def run(self, server_ip: str, server_port: int):
        self.server_id = await self.client.connect(
            server_ip=server_ip,
            server_port=server_port,
        )
        print("Connected to Server")

        try:
            game_task = asyncio.create_task(self.game_loop())
            send_task = asyncio.create_task(self.send_loop())

            await asyncio.gather(game_task, send_task)

        finally:
            print("Shutting down")
            self.running = False
            await self.client.stop()
            pygame.quit()


if __name__ == '__main__':
    game = GameClient(cert_file="../../certificate/cert.pem")
    asyncio.run(game.run(server_ip=SERVER_IP, server_port=SERVER_PORT))
