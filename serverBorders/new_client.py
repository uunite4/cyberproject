import asyncio
import json

import pygame

from wrappers.client_wrapper import QuicClient

# Visual Settings
WIDTH, HEIGHT = 700, 500
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("Arial", 24)


class LoginClient:

    def __init__(self):
        self.status_msg = None
        self.login_server_id = None

        # event used to signal server response
        self.response_event = asyncio.Event()

        self.client = QuicClient(
            cert_file="../certificate/cert.pem",
            on_receive=self.on_receive
        )

    def on_receive(self, connection_id: int, data: bytes):

        if connection_id == self.login_server_id:
            self.status_msg = data.decode().split("=")
            print(f"login server: {self.status_msg}")

            # notify response received
            self.response_event.set()

    def send_to_login_server(self, data):
        self.client.send(self.login_server_id, data)

    async def run(self):

        self.login_server_id = await self.client.connect(
            server_ip="127.0.0.1",
            server_port=8080,
        )
        print('connected to server')

        try:

            pygame_task = asyncio.create_task(self.main_menu())
            await asyncio.gather(pygame_task)
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Client shutting down...")

        finally:
            await self.client.stop()
            print("Client shut down")

    async def main_menu(self):
        # Variables to track what we are typing
        username = ""
        password = ""
        active_field = "username"  # Toggle between username and password
        mode = "START"  # START, LOGIN_INPUT, SIGNUP_INPUT
        status_msg = "Waiting for input..."  # This is our 'waiting room'

        running = True
        while running:
            await asyncio.sleep(0.001)
            screen.fill(WHITE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if mode == "START":
                        if event.key == pygame.K_l:
                            mode = "LOGIN_INPUT"
                        if event.key == pygame.K_s:
                            mode = "SIGNUP_INPUT"

                    elif "INPUT" in mode:
                        if event.key == pygame.K_ESCAPE:
                            mode = "START"
                            # Optional: Clear the text so it's empty when you come back
                            username = ""
                            password = ""
                            status_msg = "Waiting for input..."
                        if event.key == pygame.K_TAB:  # Switch fields
                            active_field = "password" if active_field == "username" else "username"
                        elif event.key == pygame.K_RETURN:  # SEND TO SERVER
                            print("username: " + username)
                            print("password: " + password)
                            status_msg = await self.send_to_server(
                                username,
                                password,
                                "LOGIN" if mode == "LOGIN_INPUT" else "SIGNUP"
                            )
                        elif event.key == pygame.K_BACKSPACE:
                            if active_field == "username":
                                username = username[:-1]
                            else:
                                password = password[:-1]
                        else:
                            if active_field == "username":
                                username += event.unicode
                            else:
                                password += event.unicode

            # --- DRAWING LOGIC ---
            if mode == "START":
                self.draw_text("Welcome to the MMORPG", 230, 150)
                self.draw_text("Press 'L' for Login", 250, 250)
                self.draw_text("Press 'S' for Signup", 250, 300)

            elif "INPUT" in mode:
                self.draw_text(f"Mode: {mode}", 50, 50)
                self.draw_text(f"Username: {username} {'|' if active_field == 'username' else ''}", 100, 150)
                self.draw_text(f"Password: {'*' * len(password)} {'|' if active_field == 'password' else ''}", 100, 200)
                self.draw_text("Press TAB to switch, ENTER to submit, ESC to go back", 100, 300)

                if status_msg[1] == "ERROR: with signup":
                    self.draw_text("SignUp failed!", 100, 400, color=(255, 0, 0))
                elif status_msg[1] == "ERROR: with login":
                    self.draw_text("Login Failed!", 100, 400, color=(255, 0, 0))
                elif status_msg[1] == "ERROR: username is empty" or status_msg[1] == "ERROR: password is empty":
                    self.draw_text("password or username is empty", 100, 400, color=(255, 0, 0))
                else:
                    self.draw_text("the key: " + status_msg[1], 100, 400, color=(255, 0, 0))
                if status_msg[2] == "NO USER FOUND":
                    self.draw_text("NO USER FOUND ", 100, 460, color=(255, 0, 0))
                elif status_msg[2] == "User already found":
                    self.draw_text("USER FOUND ", 100, 460, color=(255, 0, 0))
                elif status_msg[1] == "ERROR: username is empty" or status_msg[1] == "ERROR: password is empty":
                    self.draw_text("password or username is empty", 100, 400, color=(255, 0, 0))
                else:
                    self.draw_text("the next server: " + status_msg[2], 100, 460, color=(255, 0, 0))
            pygame.display.flip()

    def draw_text(self, text, x, y, color=BLACK):
        img = font.render(text, True, color)
        screen.blit(img, (x, y))

    async def send_to_server(self, u, p, action):
        data = json.dumps({"username": u, "password": p, "action": action})

        # reset event before sending
        self.response_event.clear()
        self.send_to_login_server(data.encode())

        try:
            # wait for server response
            await asyncio.wait_for(self.response_event.wait(), timeout=2)

        except asyncio.TimeoutError:
            print("Connection timeout")
            return ["ERROR", "TIMEOUT", ""]

        status_msg = self.status_msg
        self.status_msg = None

        return status_msg


if __name__ == '__main__':
    c = LoginClient()
    asyncio.run(c.run())
