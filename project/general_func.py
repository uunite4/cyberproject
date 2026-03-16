import math
import settings as s
import random
from Player import *

def distance(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def order(list_dis,list_id,list_pos):
    n = len(list_dis)
    for i in range(n):
        for j in range(0, n - i - 1):
            if list_dis[j] > list_dis[j + 1]:
                list_dis[j], list_dis[j + 1] = list_dis[j + 1], list_dis[j]
                list_id[j], list_id[j + 1] = list_id[j + 1], list_id[j]
                list_pos[j], list_pos[j + 1] = list_pos[j + 1], list_pos[j]
    return list_id,list_pos

def vector(x1,y1,x2,y2):
    """
    returns a tuple:
    if the first variable is 0 its go straight up or down depending on the second variable
    if not its:
    (speed*first_variable, speed*second_variable*first_variable)
    """
    dx = x2-x1
    dy = y2-y1
    if dx==0:
        if dy>0:
            dy=1
        if dy<0:
            dy=-1
        return (0,dy)
    slope = dy/dx
    if dx<0:
        dx = -1
    elif dx>0:
        dx = 1
    return(dx,slope)

def jumps(size,slope):
    ab = abs(slope)
    if ab==0:
        return size
    elif ab<=1:
        return size*ab
    elif ab>1:
        return size/ab

def rand_pos(radius,enemy):
    r = radius
    ex = int(enemy.entity.x)
    ey = int(enemy.entity.y)
    rand_x = random.randint(ex - r, ex + r)
    rand_y = random.randint(ey - r, ey + r)
    return rand_x,rand_y

def next_pos(sx,sy,tx,ty,speed): #start x,y ; target x,y ; speed
    dir,slope = vector(sx,sy,tx,ty)
    if dir==0:
        nx = sx
        ny = sy + slope*speed
    else:
        nx = sx + dir*speed
        ny = sy + dir*speed*slope
    return nx,ny


def next_pos2(sx, sy, tx, ty, speed):
    dist = distance(sx, sy, tx, ty)
    if dist < speed:
        return tx, ty  # Arrived at target

    # Calculate angle to target
    angle = math.atan2(ty - sy, tx - sx)
    nx = sx + math.cos(angle) * speed
    ny = sy + math.sin(angle) * speed
    return nx, ny

def in_view(sx, sy, tx, ty):

    start = pygame.Vector2(sx, sy)
    target = pygame.Vector2(tx, ty)

    direction: pygame.Vector2 = pygame.Vector2(target) - pygame.Vector2(start)
    dist = direction.length()

    if dist == 0:
        return True

    direction = direction.normalize()

    step_size = TILE_SIZE / 2  # smaller = more accurate
    steps = int(dist / step_size)

    pos = pygame.Vector2(start)

    for _ in range(steps):
        if check_collision_with_stone(pos.x, pos.y, TILE_SIZE):
            return False
        pos += direction * step_size

    return True


def get_dir_from_vector(dx, dy):
    if dx == 0 and dy == 0:
        return None

    # Calculate angle in degrees (0 is East, 90 is South)
    angle = math.degrees(math.atan2(dy, dx))
    if angle < 0:
        angle += 360

    # Map the 360 degrees into 8 segments of 45 degrees
    # 1:E, 2:SE, 3:S, 4:SW, 5:W, 6:NW, 7:N, 8:NE
    if 337.5 <= angle or angle < 22.5: return 1  # East
    if 22.5 <= angle < 67.5: return 2  # South-East
    if 67.5 <= angle < 112.5: return 3  # South
    if 112.5 <= angle < 157.5: return 4  # South-West
    if 157.5 <= angle < 202.5: return 5  # West
    if 202.5 <= angle < 247.5: return 6  # North-West
    if 247.5 <= angle < 292.5: return 7  # North
    if 292.5 <= angle < 337.5: return 8  # North-East
    return 1