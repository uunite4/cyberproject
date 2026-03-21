import random
import math
from map_data import *
import pygame
from classes.Player import *
from SETTINGS import *


screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
grassb = pygame.image.load(grass).convert_alpha()
stoneb = pygame.image.load(stone).convert_alpha()
lavab = pygame.image.load(lava).convert_alpha()
treeb =pygame.image.load(tree).convert_alpha()
peselb= pygame.image.load(pesel).convert_alpha()
marbleb = pygame.image.load(marble).convert_alpha()
bitmikdashb = pygame.image.load(bitmikdash).convert_alpha()
ostoneb = pygame.image.load(ostone).convert_alpha()
logb = pygame.image.load(log).convert_alpha()
tree_1b = pygame.image.load(tree_1).convert_alpha()
tree_2b = pygame.image.load(tree_2).convert_alpha()


#####
def create_massive_map(width, height):
    # 1. יצירת בסיס המפה - מתחילים עם אדמה סלעית (O)
    new_map = [["O" for _ in range(width)] for _ in range(height)]

    center_x, center_y = width // 2, height // 2
    # חישוב הרדיוס המקסימלי לפי חצי מהצד הקצר של המפה
    max_radius = min(center_x, center_y)

    # הגדרת רדיוסים לפי אחוזים מהמרחק המקסימלי
    # (מתחילים מעבר למקדש שתופס בערך 20-30 פיקסלים מהמרכז)
    r_marble_limit = max_radius * 0.33  # שליש ראשון: שייש
    r_grass_limit = max_radius * 0.66  # שליש שני: דשא
    # כל מה שמעבר ל-66% מהרדיוס הוא אדמה סלעית (O)

    # 2. שלב א': חלוקת האזורים (Biomes)
    temple_half = 20  # חצי מ-40 כדי ליצור ריבוע 40x40

    for y in range(height):
        for x in range(width):
            # בדיקה אם אנחנו בתוך המקדש (40 על 40 באמצע)
            if (center_x - temple_half <= x < center_x + temple_half) and \
                    (center_y - temple_half <= y < center_y + temple_half):
                new_map[y][x] = "B"
                continue

            # חישוב מרחק מהמרכז לצורך קביעת האזור
            dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

            if dist < r_marble_limit:
                new_map[y][x] = "V"  # שייש
            elif dist < r_grass_limit:
                new_map[y][x] = "G"  # דשא
            # השאר כבר מוגדר כ-O

    # 3. שלב ב': הוספת מקבצים (Clusters)
    def add_clusters(tile_type, min_dist, max_dist, num_clusters, cluster_size):
        for _ in range(num_clusters):
            # בחירת מיקום רנדומלי בתוך טבעת האזור
            angle = random.uniform(0, 2 * math.pi)
            d = random.uniform(min_dist, max_dist)
            seed_x = int(center_x + d * math.cos(angle))
            seed_y = int(center_y + d * math.sin(angle))

            for dy in range(-cluster_size, cluster_size + 1):
                for dx in range(-cluster_size, cluster_size + 1):
                    nx, ny = seed_x + dx, seed_y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if math.sqrt(dx ** 2 + dy ** 2) < cluster_size * random.uniform(0.7, 1.3):
                            # לא דורסים את המקדש
                            if new_map[ny][nx] != "B":
                                new_map[ny][nx] = tile_type

    # הוספת מקבצי סלעים (S) באזור הדשא
    add_clusters("S", r_marble_limit, r_grass_limit, num_clusters=20, cluster_size=3)

    # הוספת אגמי לבה (L) באזור האדמה הסלעית
    add_clusters("L", r_grass_limit, max_radius, num_clusters=15, cluster_size=6)

    # 4. שלב ג' - פריטים בודדים (עצים ופסלים)
    for y in range(height):
        for x in range(width):
            # עצים בדשא (G)
            if new_map[y][x] == "G" and random.random() < 0.02:
                new_map[y][x] = "T"
            # פסלים בשייש (V)
            elif new_map[y][x] == "V" and random.random() < 0.01:
                new_map[y][x] = "P"

    return new_map
def save_to_mapdata(game_map):
    with open("map_data.py", "w", encoding="utf-8") as f:
        f.write("MAP = [\n")
        for row in game_map:
            f.write(f"    {row},\n")
        f.write("]\n")
    print("המפה נשמרה בהצלחה בתוך map_data.py!")
##create_massive_map(MAP_W//40,MAP_H//40 )
#########save_to_mapdata(my_map)
####




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

def draw_map(screen, map_data, cam_x, cam_y, window_w, window_h, tile_size=TILE_SIZE):
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

            if tile == 'S':
                screen.blit(stoneb, (px, py))
            elif tile == 'L':
                screen.blit(lavab, (px, py))
            elif tile == 'P':
                screen.blit(peselb, (px, py))
            elif tile == 'G':
                screen.blit(grassb, (px, py))
            elif tile == 'V':
                screen.blit(marbleb, (px, py))
            elif tile == 'O':
                screen.blit(ostoneb, (px, py))
            elif tile == 'T':
                screen.blit(treeb, (px, py))
            else:
                screen.blit(peselb, (px, py))

