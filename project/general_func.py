import math


def distance(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)


def order(arr):
    sorted_arr = sorted(arr, key = lambda x:x[1])
    arr_ip,arr_id = [],[]
    for item in sorted_arr:
        arr_id.append(item[0])
        arr_ip.append(item[1])
    return  (arr_id,arr_ip)

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
