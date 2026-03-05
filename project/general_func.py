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

def draw_enemy(screen, enemys, cam_x, cam_y, ENEMY_SPRITES, DEFAULT_SPRITE):
    for eid, e in enemys.items():
        ex = int(e.x - cam_x - s.ENEMY_SIZE // 2)
        ey = int(e.y - cam_y - s.ENEMY_SIZE // 2)

        sprite = ENEMY_SPRITES.get(e.dir, DEFAULT_SPRITE)

        screen.blit(sprite, (ex, ey))
        #need to add the attack for monster
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
    ex = enemy.entity.x
    ey = enemy.entity.y
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

def in_view(sx,sy,tx,ty):
    dir, slope = vector(sx,sy,tx,ty)
    if dir==0:
        while (sy < ty and slope==-1) or (sy > ty and slope==1):
            if check_collision_with_stone(TILE_SIZE,sx,sy):
                return False
            sy += slope*TILE_SIZE
        return True
    else:
        jump = jumps(TILE_SIZE, slope)
        while (sx < tx and dir==-1) or (sx > tx and dir==1):
            if check_collision_with_stone(TILE_SIZE, sx, sy):
                return False
            sx += dir * jump
            sy += slope*dir*jump
        return True