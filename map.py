import random
import pygame
from map_data import *
from Player import *
from settings import *


screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
grassb = pygame.image.load(grass).convert_alpha()
stoneb = pygame.image.load(stone).convert_alpha()
lavab = pygame.image.load(lava).convert_alpha()
def create_massive_map():
    # יצירת מפה ריקה עם "שטח פתוח"
    grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # 1. יצירת המבנה המרכזי (b)
    start_x = (WIDTH - BUILDING_SIZE) // 2
    start_y = (HEIGHT - BUILDING_SIZE) // 2-80

    for y in range(start_y, start_y + BUILDING_SIZE):
        for x in range(start_x, start_x + BUILDING_SIZE):
            grid[y][x] = 'b'

    # 2. יצירת קבוצות אבנים (x)
    num_clusters = 200  # כמות קבוצות מפוזרות
    for _ in range(num_clusters):
        cx = random.randint(0, WIDTH - 1)
        cy = random.randint(0, HEIGHT - 1)

        # כל קבוצה מכילה כמה אבנים צמודות
        for _ in range(random.randint(10, 30)):
            nx = cx + random.randint(-1, 3)
            ny = cy + random.randint(-1, 2)
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if grid[ny][nx] == ' ':  # לא לדרוס את המבנה
                    grid[ny][nx] = 'x'

    # 3. שמירה לקובץ טקסט
    with open("map_data.py", "w") as f:
        f.write("MAP = [\n")
        for row in grid:
            # כל שורה נכתבת כרשימה: [' ', 'x', 'b'...]
            f.write(f"    {row},\n")
        f.write("]\n")




def build_map_surface(MAP, TILE_SIZE=40):

    map_height_tiles = len(MAP)
    map_width_tiles = len(MAP[0])

    pixel_width = map_width_tiles * TILE_SIZE
    pixel_height = map_height_tiles * TILE_SIZE


    surf = pygame.Surface((pixel_width, pixel_height))




    for row_index, row in enumerate(MAP):
        for col_index, tile in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE

            if tile == 'x':

                surf.blit(stone, (x, y))
            elif tile == ' ':

                surf.blit(grass, (x, y))

            elif tile == 'b':
                surf.blit((0,0,0), (x, y))
    return surf

def load_map_from_txt(filename):
    with open(filename, 'r') as f:
        return [list(line.strip()) for line in f.readlines()]



def draw_map(screen, map_data, cam_x, cam_y, window_w, window_h, tile_size=40):
    # חישוב אינדקסים של התיילים שרואים כרגע על המסך
    start_tx = max(0, cam_x // tile_size)
    start_ty = max(0, cam_y // tile_size)

    # כמה תיילים נכנסים ברוחב ובגובה המסך (מוסיפים 2 לביטחון)
    end_tx = min(len(map_data[0]), start_tx + (window_w // tile_size) + 2)
    end_ty = min(len(map_data), start_ty + (window_h // tile_size) + 2)

    # לולאת הציור
    for ty in range(start_ty, end_ty):
        for tx in range(start_tx, end_tx):
            tile = map_data[ty][tx]

            # מיקום הציור על המסך
            px = tx * tile_size - cam_x
            py = ty * tile_size - cam_y

            if tile == 'x':
                screen.blit(stoneb, (px, py))
            elif tile == 'b':
                # כאן אפשר לשים תמונה של מבנה, כרגע נשתמש באבן לניסוי
                screen.blit(lavab, (px, py))
            else:
                screen.blit(grassb, (px, py))

#create_massive_map()
