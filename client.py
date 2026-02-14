import pygame
import socket

# Visual Settings
WIDTH, HEIGHT = 700, 500
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("Arial", 24)


def draw_text(text, x, y, color=BLACK):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def main_menu():
    # Variables to track what we are typing
    username = ""
    password = ""
    active_field = "username"  # Toggle between username and password
    mode = "START"  # START, LOGIN_INPUT, SIGNUP_INPUT
    status_msg = "Waiting for input..."  # This is our 'waiting room'

    running = True
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if mode == "START":
                    if event.key == pygame.K_l: mode = "LOGIN_INPUT"
                    if event.key == pygame.K_s: mode = "SIGNUP_INPUT"

                elif "INPUT" in mode:
                    if event.key == pygame.K_TAB:  # Switch fields
                        active_field = "password" if active_field == "username" else "username"
                    elif event.key == pygame.K_RETURN:  # SEND TO SERVER
                        status_msg = send_to_server(username, password, "LOGIN" if mode == "LOGIN_INPUT" else "SIGNUP")
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
            draw_text("Welcome to the MMORPG", 230, 150)
            draw_text("Press 'L' for Login", 250, 250)
            draw_text("Press 'S' for Signup", 250, 300)

        elif "INPUT" in mode:
            draw_text(f"Mode: {mode}", 50, 50)
            draw_text(f"Username: {username} {'|' if active_field == 'username' else ''}", 100, 150)
            draw_text(f"Password: {'*' * len(password)} {'|' if active_field == 'password' else ''}", 100, 200)
            draw_text("Press TAB to switch, ENTER to submit", 100, 300)
            draw_text("the key: "+status_msg[1], 100, 400, color=(255, 0, 0))
            draw_text("the next server: "+status_msg[2], 100, 460, color=(255, 0, 0))
        pygame.display.flip()


def send_to_server(u, p, action):
    data = f"{u}={p}={action}"
    try:
        s = socket.socket()
        s.settimeout(2) # <--- ADD THIS: Don't wait more than 2 seconds
        s.connect(("127.0.0.1", 8080))
        s.send(data.encode())
        response = s.recv(1024).decode()
        s.close()
        print(response)
        answer = response.split("=")
        return answer # Return the actual answer to the UI
    except Exception as e:
        print(f"Connection Error: {e}")
        return "CONNECTION_ERROR"


if __name__ == "__main__":
    main_menu()