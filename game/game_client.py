import asyncio
import struct

import pygame

from game.game_server import SERVER_IP, SERVER_PORT
from wrappers.client_wrapper import QuicClient

DISPLAY_FPS: int = 60
SEND_FPS: int = 10

WIDTH: int = 320 * 2
HEIGHT: int = 200 * 2

"""

skip interpolating own player

add delta time calculations

add lerp between last position

instead of using "server_tick" to control the send fps,
made a new task that runs at the given fps

build a networking framework

"""


class ClientPlayer(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, group):
        super().__init__(group)
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=pos)

    def set_pos(self, pos: pygame.Vector2):
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

        self.player_pos = pygame.Vector2()
        self.delta_time = 0
        self.tick = 0

    def serialize(self):

        x = int(self.player_direction.x) + 1  # -1,0,1 -> 0,1,2
        y = int(self.player_direction.y) + 1  # -1,0,1 -> 0,1,2

        return struct.pack(
            'B',
            (x << 2) | y  # store x in high 2 bits, y in low 2 bits
        )

    def deserialize(self, data: bytes):

        player_count = struct.unpack_from('H', data)[0]
        offset = struct.calcsize('H')

        players = []
        for _ in range(player_count):
            player_id, x, y = struct.unpack_from("Hhh", data, offset)
            offset += struct.calcsize('Hhh')
            players.append({
                "id": player_id,
                "x": x,
                "y": y
            })

        return players

    def upsert_player(self, player_id: int, pos: pygame.Vector2):
        if player_id in self.players:
            player = self.players[player_id]
            player.set_pos(pos)
            return player

        player = ClientPlayer(pos, self.sprite_group)
        self.players[player_id] = player
        return player

    def on_receive(self, connection_id: int, data: bytes):
        if connection_id == self.server_id:

            player_data = self.deserialize(data)

            for p in player_data:
                self.upsert_player(
                    p['id'],
                    pygame.Vector2(p['x'], p['y'])
                )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _update_self_pos(self):
        keys = pygame.key.get_pressed()

        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y = -1
        if keys[pygame.K_s]:
            direction.y = 1
        if keys[pygame.K_a]:
            direction.x = -1
        if keys[pygame.K_d]:
            direction.x = 1

        self.player_direction = direction

    def _update_other_pos(self):
        pass

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.sprite_group.draw(self.screen)
        pygame.display.update()

    def update(self):
        self.handle_events()
        self._update_self_pos()
        self._update_other_pos()
        self.draw()

        # only send at the SEND FPS
        if self.tick % (1 / SEND_FPS):
            self.client.send(self.server_id, self.serialize())

    async def run(self, server_ip: str, server_port: int):
        self.server_id = await self.client.connect(
            server_ip=server_ip,
            server_port=server_port,
        )
        print("Connected to Server")

        try:
            while self.running:
                self.delta_time = self.clock.tick(DISPLAY_FPS) / 1000.0
                pygame.display.set_caption(str((1 / self.delta_time).__round__(1)))
                self.tick += 1
                self.update()

                await asyncio.sleep(0.001)
        finally:
            print("Shutting down")
            await self.client.stop()
            pygame.quit()


if __name__ == '__main__':
    game = GameClient(cert_file="../certificate/cert.pem")
    asyncio.run(game.run(server_ip=SERVER_IP, server_port=SERVER_PORT))
